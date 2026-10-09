"""Monitor-Erkennung: kscreen-doctor (KDE, X11 + Wayland), Fallback xrandr (X11)."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass

from .geometry import Rect
from .i18n import FcwmError

# kscreen Rotationswerte: 1=normal, 2=links (90°), 4=180°, 8=rechts (270°)
_ROTATED = {2, 8}


@dataclass
class Monitor:
    name: str
    geometry: Rect              # logische Koordinaten (nach Rotation und Skalierung)
    scale: float = 1.0
    primary: bool = False
    workarea: Rect | None = None  # Arbeitsbereich ohne Panels (sofern das Backend ihn kennt)

    def to_dict(self) -> dict:
        return {"name": self.name, "geometry": self.geometry.as_list(), "scale": self.scale,
                "primary": self.primary,
                "workarea": self.workarea.as_list() if self.workarea else None}


def _from_kscreen() -> list[Monitor]:
    out = subprocess.run(["kscreen-doctor", "-j"], capture_output=True, text=True,
                         check=True, timeout=10).stdout
    data = json.loads(out)
    mons = []
    for o in data.get("outputs", []):
        if not (o.get("enabled") and o.get("connected")):
            continue
        mode = next((m for m in o.get("modes", []) if m["id"] == o.get("currentModeId")), None)
        if mode:
            w, h = mode["size"]["width"], mode["size"]["height"]
        else:
            w, h = o["size"]["width"], o["size"]["height"]
        if o.get("rotation") in _ROTATED:
            w, h = h, w
        scale = float(o.get("scale") or 1.0)
        mons.append(Monitor(
            name=o["name"],
            geometry=Rect(int(o["pos"]["x"]), int(o["pos"]["y"]), round(w / scale), round(h / scale)),
            scale=scale,
            primary=o.get("priority") == 1,
        ))
    return mons


_XRANDR_RE = re.compile(r"^\s*\d+:\s+[+*]*(\S+)\s+(\d+)/\d+x(\d+)/\d+\+(-?\d+)\+(-?\d+)\s+(\S+)")


def _from_xrandr() -> list[Monitor]:
    out = subprocess.run(["xrandr", "--listmonitors"], capture_output=True, text=True,
                         check=True, timeout=10).stdout
    mons = []
    for line in out.splitlines():
        m = _XRANDR_RE.match(line)
        if m:
            _, w, h, x, y, name = m.groups()
            mons.append(Monitor(name, Rect(int(x), int(y), int(w), int(h)), primary="*" in line))
    return mons


def detect_monitors() -> list[Monitor]:
    """Liefert die Monitore, sortiert von links nach rechts (dann oben nach unten)."""
    errors = []
    for tool, fn in (("kscreen-doctor", _from_kscreen), ("xrandr", _from_xrandr)):
        if not shutil.which(tool):
            continue
        try:
            mons = fn()
            if mons:
                return sorted(mons, key=lambda m: (m.geometry.x, m.geometry.y))
        except Exception as e:  # noqa: BLE001 – nächsten Provider versuchen
            errors.append(f"{tool}: {e}")
    raise FcwmError("no_monitors_detected", errors="; ".join(errors))
