"""Hide/color the title bars of EVE clients – via KWin window rules.

KWin does not allow scripts to set a window's color scheme; window rules
(System Settings → Window Management → Window Rules) can. We maintain only our
own rules there, with the prefix "fcwm-", and leave all others untouched.
Colors are stored as small color schemes under ~/.local/share/color-schemes/FCWM-<hex>.colors.

Writing is done with kwriteconfig6 (like System Settings itself), after which KWin reloads the
rules via D-Bus.
"""
from __future__ import annotations

import hashlib
import logging
import os
import re
import shutil
import subprocess
from pathlib import Path

from .config import Config

log = logging.getLogger("fcwm")

RULES_FILE = "kwinrulesrc"
PREFIX = "fcwm-"
LEGACY_PREFIXES = ("evewm-",)   # former project name – we clean up its rules too


def _ours(rule_id: str) -> bool:
    return rule_id.startswith(PREFIX) or rule_id.startswith(LEGACY_PREFIXES)
# all keys we set in a rule – for clean removal
_KEYS = ["Description", "wmclass", "wmclassmatch", "wmclasscomplete", "title", "titlematch", "types",
         "decocolor", "decocolorrule", "noborder", "noborderrule"]
_SCHEME_DIR = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "color-schemes"


def available() -> bool:
    return bool(shutil.which("kwriteconfig6") and shutil.which("kreadconfig6"))


def _read(group: str, key: str) -> str:
    return subprocess.run(["kreadconfig6", "--file", RULES_FILE, "--group", group, "--key", key],
                          capture_output=True, text=True).stdout.strip()


def _write(group: str, key: str, value: str | None) -> None:
    cmd = ["kwriteconfig6", "--file", RULES_FILE, "--group", group, "--key", key]
    cmd += ["--delete"] if value is None else [value]
    subprocess.run(cmd, check=True)


def _hex(color: str) -> str | None:
    m = re.fullmatch(r"#?([0-9a-fA-F]{6})", color or "")
    return m.group(1).lower() if m else None


def _scheme(color: str) -> str:
    """Creates (if needed) a color scheme for the title bar and returns its name."""
    h = _hex(color)
    name = f"FCWM-{h}"
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    dim = lambda v: int(v * 0.55)
    fg = "255,255,255" if (0.299 * r + 0.587 * g + 0.114 * b) < 150 else "20,20,20"
    rgb, rgb_dim = f"{r},{g},{b}", f"{dim(r)},{dim(g)},{dim(b)}"
    _SCHEME_DIR.mkdir(parents=True, exist_ok=True)
    (_SCHEME_DIR / f"{name}.colors").write_text(
        f"[General]\nColorScheme={name}\nName={name}\n\n"
        f"[WM]\nactiveBackground={rgb}\nactiveBlend={rgb}\nactiveForeground={fg}\n"
        f"inactiveBackground={rgb_dim}\ninactiveBlend={rgb_dim}\ninactiveForeground=200,200,200\n\n"
        f"[Colors:Header]\nBackgroundNormal={rgb}\nForegroundNormal={fg}\n\n"
        f"[Colors:Header][Inactive]\nBackgroundNormal={rgb_dim}\nForegroundNormal=200,200,200\n",
        encoding="utf-8")
    return name


def _js_regex(pattern: str) -> str:
    # KWin (QRegularExpression/PCRE) understands named groups (?P<name>…) – pass through unchanged
    return pattern


# Coloring title bars does not work reliably yet: hidden in the web UI and not applied. Configured colors
# stay in the config; with this off, the next sync removes any color rules written earlier.
COLORS_ENABLED = False


def desired_rules(cfg: Config) -> dict[str, dict[str, str]]:
    """Rule ID -> keys/values. Character rules first (KWin applies the first matching one)."""
    tb = cfg.titlebar or {}
    cls = cfg.class_re.pattern if cfg.class_re else ""
    base = {"wmclass": cls, "wmclassmatch": "3" if cls else "0", "wmclasscomplete": "false", "types": "1"}
    rules: dict[str, dict[str, str]] = {}

    def props(color: str | None) -> dict[str, str]:
        p = {}
        if COLORS_ENABLED and color and _hex(color):
            p.update(decocolor=_scheme(color), decocolorrule="2")
        if tb.get("hide"):
            p.update(noborder="true", noborderrule="2")
        return p

    for char, c in sorted(cfg.characters.items()):
        pr = props(c.get("color"))
        if "decocolor" not in pr:
            continue
        rid = PREFIX + "char-" + hashlib.sha1(char.encode()).hexdigest()[:10]
        rules[rid] = {"Description": f"FleetCommander: {char}", **base,
                      "title": f"^EVE - {re.escape(char)}$", "titlematch": "3", **pr}
    pr = props(tb.get("color"))
    if pr:
        rules[PREFIX + "all"] = {"Description": "FleetCommander: all EVE clients", **base,
                                 "title": _js_regex(cfg.caption_re.pattern), "titlematch": "3", **pr}
    return rules


def apply_rules(cfg: Config) -> int:
    """Syncs our rules with the configuration. Returns: number of active rules."""
    if not available():
        log.warning("kwriteconfig6/kreadconfig6 not found – title bars are left unchanged")
        return 0
    return _write_rules(desired_rules(cfg))


def remove_rules() -> int:
    """Remove all own rules (fcwm-*) and color schemes – for `fcwm cleanup`.
    Returns: number of removed rules."""
    removed = 0
    if available():
        removed = sum(1 for r in _read("General", "rules").split(",") if _ours(r))
        if removed:
            _write_rules({})
    for f in [*_SCHEME_DIR.glob("FCWM-*.colors"), *_SCHEME_DIR.glob("EVEWM-*.colors")]:
        f.unlink(missing_ok=True)
    return removed


def _write_rules(rules: dict[str, dict[str, str]]) -> int:
    current = [r for r in _read("General", "rules").split(",") if r]
    others = [r for r in current if not _ours(r)]
    for rid in (r for r in current if _ours(r)):
        for k in _KEYS:
            _write(rid, k, None)
    for rid, kv in rules.items():
        for k, v in kv.items():
            _write(rid, k, v)
    order = list(rules) + others          # our rules first
    if order:
        _write("General", "rules", ",".join(order))
        _write("General", "count", str(len(order)))
    else:                                  # the way System Settings writes an empty list
        _write("General", "rules", "")
        _write("General", "count", None)
    subprocess.run(["busctl", "--user", "call", "org.kde.KWin", "/KWin", "org.kde.KWin", "reconfigure"],
                   capture_output=True)
    return len(rules)


def sync(cfg: Config) -> None:
    """Only touch rules if we want some or old ones of ours still exist."""
    if not available():
        return
    ours = [r for r in _read("General", "rules").split(",") if _ours(r)]
    if ours or desired_rules(cfg):
        apply_rules(cfg)
