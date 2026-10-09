"""Laden/Validieren der Konfiguration (YAML oder JSON)."""
from __future__ import annotations

import json
import os
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from .geometry import GridSpec, Insets
from .i18n import ConfigError, FcwmError

DEFAULT_PATHS = [
    Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "fcwm" / "config.yaml",
    Path(__file__).resolve().parent.parent / "config.yaml",
]


@dataclass
class MonitorCfg:
    alias: str
    output: str | None          # Anschlussname, z. B. "DP-1"
    index: int | None           # alternativ: Index (0 = ganz links)
    grid: GridSpec
    reserve: Insets | str       # "auto" oder Insets (Panel-Abzug)
    padding: Insets


@dataclass
class Assignment:
    char: str
    monitor: str
    slot: int
    span: tuple[int, int] = (1, 1)
    sub: int | None = None      # Zelle im Subgrid von `slot` ("center:1.3" -> slot 1, sub 3)


def parse_slot(text) -> tuple[int, int | None]:
    """"3" -> (3, None), "1.3" -> (1, 3)."""
    main, _, sub = str(text).strip().partition(".")
    return int(main or 0), (int(sub) if sub != "" else None)


def slot_text(slot: int, sub: int | None) -> str:
    return f"{slot}" if sub is None else f"{slot}.{sub}"


@dataclass
class Profile:
    name: str
    description: str = ""
    grids: dict[str, GridSpec] = field(default_factory=dict)
    assign: list[Assignment] = field(default_factory=list)
    fill: list[str] = field(default_factory=list)   # Monitore für nicht zugewiesene Clients
    focus: str | None = None
    stack_overflow: bool = True   # kein freier Slot mehr -> reihum auf fill-Slots stapeln
    disabled: list[str] = field(default_factory=list)  # Monitore, die dieses Profil nicht verwendet
    blocked: list["BlockedCell"] = field(default_factory=list)  # freigehaltene Felder (Browser, RIFT …)
    subgrids: dict[tuple[str, int], GridSpec] = field(default_factory=dict)  # (monitor, slot) -> Raster in der Zelle
    overflow: list["OverflowCell"] = field(default_factory=list)  # Überlauf-Felder in Reihenfolge
    hotkey: str = ""                                  # globaler Kurzbefehl: dieses Profil anwenden
    stack_hotkeys: dict[str, str] = field(default_factory=dict)  # "center:1" -> Kurzbefehl zum Durchschalten
    # Vorschau-Leiste auf einem Stapel: "center:1" -> {mode: stack|all, edge: bottom|top|left|right, size: %, show}
    stack_previews: dict[str, dict] = field(default_factory=dict)


@dataclass
class OverflowCell:
    """Nimmt Clients auf, für die kein Auffüll-Feld mehr frei ist (als Stapel). `max` begrenzt die
    Anzahl Charaktere im Feld; das letzte Überlauf-Feld nimmt immer alle übrigen auf."""
    monitor: str
    slot: int
    sub: int | None = None
    max: int | None = None


@dataclass
class BlockedCell:
    """Ein Feld, das nie mit EVE-Clients belegt wird. Optional landet dort ein anderes Fenster,
    dessen Titel oder Fensterklasse auf `match` passt (Regex, ohne Gross-/Kleinschreibung)."""
    monitor: str
    slot: int
    label: str = ""
    match: str = ""
    sub: int | None = None
    preview: str = ""           # "", "all" (alle Clients) oder "hidden" (nur verdeckte/minimierte)
    preview_show: str = "always"  # "always" oder "eve" (nur sichtbar, solange ein EVE-Client aktiv ist)


@dataclass
class Config:
    path: Path
    backend: str
    caption_re: re.Pattern
    class_re: re.Pattern | None
    gap: int
    decoration: Insets
    min_size: tuple[int, int]
    monitors: dict[str, MonitorCfg]
    profiles: dict[str, Profile]
    default_profile: str | None
    raw_text: str
    language: str | None = None
    # globale Kurzbefehle: next_profile, prev_profile, cycle_stack (Qt-Schreibweise, z. B. "Meta+Ctrl+Right")
    hotkeys: dict[str, str] = field(default_factory=dict)
    # Titelleisten der EVE-Clients: {"hide": bool, "color": "#rrggbb"|""}
    titlebar: dict = field(default_factory=dict)
    # pro Charakter: {"Name": {"color": "#rrggbb"}}
    characters: dict[str, dict] = field(default_factory=dict)
    # Trennlinie zwischen benachbarten Clients: {"width": px, "color": "#rrggbb"}
    separator: dict = field(default_factory=dict)

    @property
    def effective_gap(self) -> int:
        """Abstand zwischen Rasterzellen: die Trennlinie braucht genau ihre Breite als Lücke."""
        return max(self.gap, int(self.separator.get("width") or 0))


def _parse_assign(char: str, value, monitors: dict) -> Assignment:
    if isinstance(value, str):  # Kurzform "center:0" bzw. "center:1.3" (Subgrid)
        mon, _, slot = value.partition(":")
        main, sub = parse_slot(slot or 0)
        a = Assignment(char, mon.strip(), main, sub=sub)
    elif isinstance(value, dict):
        main, sub = parse_slot(value.get("slot", 0))
        a = Assignment(char, value["monitor"], main,
                       tuple(value.get("span", (1, 1))) if sub is None else (1, 1), sub)
    else:
        raise ConfigError("invalid_assign", char=char, value=value)
    if a.monitor not in monitors:
        raise ConfigError("unknown_monitor", mon=a.monitor, where=char)
    return a


def parse_profile(name: str, p: dict | None, monitors: dict[str, MonitorCfg]) -> Profile:
    p = p or {}
    grids = {k: GridSpec.parse(v) for k, v in (p.get("grids") or {}).items()}
    for k in grids:
        if k not in monitors:
            raise ConfigError("unknown_monitor", mon=k, where=f"{name} / grids")
    fill = p.get("fill", [])
    if fill is True:
        fill = list(monitors)
    for k in fill or []:
        if k not in monitors:
            raise ConfigError("unknown_monitor", mon=k, where=f"{name} / fill")
    disabled = list(p.get("disabled_monitors") or [])
    for k in disabled:
        if k not in monitors:
            raise ConfigError("unknown_monitor", mon=k, where=f"{name} / disabled_monitors")
    subgrids = {}
    for key, v in (p.get("subgrids") or {}).items():
        mon, _, slot = str(key).partition(":")
        if mon not in monitors:
            raise ConfigError("unknown_monitor", mon=mon, where=f"{name} / subgrids")
        subgrids[(mon, int(slot or 0))] = GridSpec.parse(v)
    overflow = []
    for v in p.get("overflow") or []:
        cell, mx = (v.get("cell"), v.get("max")) if isinstance(v, dict) else (v, None)
        mon, _, slot = str(cell).partition(":")
        if mon not in monitors:
            raise ConfigError("unknown_monitor", mon=mon, where=f"{name} / overflow")
        main, sub = parse_slot(slot or 0)
        overflow.append(OverflowCell(mon, main, sub, int(mx) if mx else None))
    stack_hotkeys = {str(k): str(v) for k, v in (p.get("stack_hotkeys") or {}).items() if v}
    stack_previews = {}
    for k, v in (p.get("stack_previews") or {}).items():
        v = v if isinstance(v, dict) else {"mode": v}
        mode = v.get("mode", "stack")
        if mode not in ("stack", "all"):
            raise ConfigError("invalid_preview", value=mode)
        stack_previews[str(k)] = {
            "mode": mode,
            "edge": v.get("edge", "bottom") if v.get("edge") in ("bottom", "top", "left", "right") else "bottom",
            "size": max(5, min(60, int(v.get("size") or 18))),
            "show": v.get("show") if v.get("show") in ("always", "eve") else "always"}
    blocked = []
    for key, v in (p.get("blocked") or {}).items():
        mon, _, slot = str(key).partition(":")
        if mon not in monitors:
            raise ConfigError("unknown_monitor", mon=mon, where=f"{name} / blocked")
        v = v if isinstance(v, dict) else {"label": v or ""}
        if v.get("match"):
            try:
                re.compile(v["match"])
            except re.error as e:
                raise ConfigError("invalid_regex", value=v["match"], error=str(e)) from e
        main, sub = parse_slot(slot or 0)
        preview = str(v.get("preview") or "")
        if preview not in ("", "all", "hidden"):
            raise ConfigError("invalid_preview", value=preview)
        show = str(v.get("show") or "always")
        blocked.append(BlockedCell(mon, main, str(v.get("label") or ""),
                                   "" if preview else str(v.get("match") or ""), sub, preview,
                                   show if show in ("always", "eve") else "always"))
    return Profile(
        name=name, description=p.get("description", "") or "", grids=grids, blocked=blocked, subgrids=subgrids,
        overflow=overflow, hotkey=str(p.get("hotkey") or ""), stack_hotkeys=stack_hotkeys,
        stack_previews=stack_previews,
        assign=[_parse_assign(c, v, monitors) for c, v in (p.get("assign") or {}).items()],
        fill=list(fill or []), focus=p.get("focus") or None,
        stack_overflow=bool(p.get("stack_overflow", True)), disabled=disabled,
    )


def _is_yaml(path: Path) -> bool:
    return path.suffix.lower() in (".yaml", ".yml")


def _yaml():
    try:
        import yaml
    except ImportError as e:
        raise FcwmError("yaml_missing") from e
    return yaml


def parse_text(text: str, path: Path) -> Config:
    data = (_yaml().safe_load(text) or {}) if _is_yaml(path) else json.loads(text)

    s = data.get("settings", {}) or {}
    match = s.get("match", {}) or {}

    monitors: dict[str, MonitorCfg] = {}
    for alias, m in (data.get("monitors") or {}).items():
        m = m or {}
        reserve = m.get("reserve", "auto")
        monitors[alias] = MonitorCfg(
            alias=alias, output=m.get("output"), index=m.get("index"),
            grid=GridSpec.parse(m.get("grid", "1x1")),
            reserve=reserve if reserve == "auto" else Insets.parse(reserve),
            padding=Insets.parse(m.get("padding", 0)),
        )
    if not monitors:
        raise ConfigError("no_monitors")

    profiles = {name: parse_profile(name, p, monitors)
                for name, p in (data.get("profiles") or {}).items()}

    default = data.get("default_profile")
    if default and default not in profiles:
        raise ConfigError("default_missing", name=default)

    return Config(
        path=path,
        backend=s.get("backend", "auto"),
        caption_re=re.compile(match.get("caption_regex", r"^EVE - (?P<char>.+)$")),
        class_re=re.compile(match["resource_class"]) if match.get("resource_class") else None,
        gap=int(s.get("gap", 0)),
        decoration=Insets.parse(s.get("decoration", 0)),
        min_size=tuple(s.get("min_size", (1024, 768))),
        monitors=monitors, profiles=profiles, default_profile=default, raw_text=text,
        language=s.get("language"),
        hotkeys={k: str(v) for k, v in (data.get("hotkeys") or {}).items() if v},
        titlebar={"hide": bool((s.get("titlebar") or {}).get("hide", False)),
                  "color": str((s.get("titlebar") or {}).get("color") or "")},
        characters={str(k): dict(v or {}) for k, v in (data.get("characters") or {}).items()},
        separator={"width": max(0, min(20, int((s.get("separator") or {}).get("width") or 0))),
                   "color": str((s.get("separator") or {}).get("color") or "#3c3c3c"),
                   "show": "eve" if (s.get("separator") or {}).get("show") == "eve" else "always"},
    )


def migrate_legacy() -> Path | None:
    """Einmalig: ~/.config/evewm (früherer Projektname) nach ~/.config/fcwm kopieren.
    Der alte Ordner bleibt als Sicherung erhalten."""
    new_dir = DEFAULT_PATHS[0].parent
    old_dir = new_dir.parent / "evewm"
    if new_dir.exists() or not old_dir.is_dir():
        return None
    names = {"config.yaml": "config.yaml", "config.yml": "config.yml", "config.json": "config.json",
             "evewm-state.json": "fcwm-state.json"}
    if not any((old_dir / n).exists() for n in names):
        return None
    new_dir.mkdir(parents=True)
    for old, new in names.items():
        if (old_dir / old).exists():
            shutil.copy2(old_dir / old, new_dir / new)
    return new_dir


def find_config(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit).expanduser()
    migrate_legacy()
    for p in DEFAULT_PATHS:
        for candidate in (p, p.with_suffix(".yml"), p.with_suffix(".json")):
            if candidate.exists():
                return candidate
    raise FcwmError("no_config", paths=", ".join(str(p) for p in DEFAULT_PATHS))


def load(explicit: str | None = None) -> Config:
    path = find_config(explicit)
    return parse_text(path.read_text(encoding="utf-8"), path)


# --------------------------------------------------------------------------
# Profile bearbeiten (Web-Editor)
#
# Das Edit-Modell ist ein einfaches Dict, wie es die Web-UI schickt:
#   {"description": str, "grids": {alias: [cols, rows]}, "fill": [alias, ...],
#    "focus": str|None, "assign": [{"char", "monitor", "slot", "span": [c, r]}]}
# --------------------------------------------------------------------------

def weights_model(g: GridSpec):
    """GridSpec -> [spaltengewichte|None, zeilengewichte|None, {zeile: spaltengewichte}|None] (None = gleichmässig)."""
    if g.uniform:
        return None
    return [list(g.col_weights) or None, list(g.row_weights) or None,
            {str(r): list(w) for r, w in g.row_col_weights} or None]


def spec_from_model(cols: int, rows: int, weights) -> GridSpec:
    cw, rw, rc = (list(weights or []) + [None, None, None])[:3]
    clean = lambda w, n: [round(float(x), 2) for x in w] if w and len(w) == n else []
    per_row = tuple(sorted((int(r), tuple(clean(w, cols))) for r, w in (rc or {}).items()
                           if 0 <= int(r) < rows and clean(w, cols)))
    return GridSpec(cols, rows, tuple(clean(cw, cols)), tuple(clean(rw, rows)), per_row)


def spec_to_raw(spec: GridSpec):
    """Kompakteste Schreibweise: "2x2" oder Dict mit nur den nötigen Gewichten."""
    if spec.uniform:
        return f"{spec.cols}x{spec.rows}"
    g = {"cols": spec.cols, "rows": spec.rows}
    if spec.col_weights and not GridSpec(spec.cols, 1, spec.col_weights).uniform:
        g["col_weights"] = list(spec.col_weights)
    if spec.row_weights and not GridSpec(1, spec.rows, (), spec.row_weights).uniform:
        g["row_weights"] = list(spec.row_weights)
    per_row = {r: list(w) for r, w in spec.row_col_weights
               if GridSpec._norm(w, spec.cols) != GridSpec._norm(spec.col_weights, spec.cols)}
    if per_row:
        g["row_col_weights"] = per_row
    return g


def profile_to_model(cfg: Config, profile: Profile) -> dict:
    return {
        "description": profile.description,
        "grids": {a: [g.cols, g.rows] for a, g in
                  ((a, profile.grids.get(a, mc.grid)) for a, mc in cfg.monitors.items())},
        # verschobene Rasterlinien: {alias: [spaltengewichte|None, zeilengewichte|None]}
        "weights": {a: weights_model(g) for a, g in
                    ((a, profile.grids.get(a, mc.grid)) for a, mc in cfg.monitors.items())
                    if not g.uniform},
        "fill": list(profile.fill),
        "focus": profile.focus,
        "stack_overflow": profile.stack_overflow,
        "disabled": list(profile.disabled),
        "blocked": [{"monitor": b.monitor, "slot": b.slot, "sub": b.sub, "label": b.label, "match": b.match,
                     "preview": b.preview, "preview_show": b.preview_show} for b in profile.blocked],
        "stack_previews": {k: dict(v) for k, v in profile.stack_previews.items()},
        "subgrids": [{"monitor": m, "slot": s, "grid": [g.cols, g.rows], "weights": weights_model(g)}
                     for (m, s), g in profile.subgrids.items()],
        "overflow": [{"monitor": o.monitor, "slot": o.slot, "sub": o.sub, "max": o.max} for o in profile.overflow],
        "hotkey": profile.hotkey,
        "stack_hotkeys": dict(profile.stack_hotkeys),
        "assign": [{"char": a.char, "monitor": a.monitor, "slot": a.slot, "sub": a.sub, "span": list(a.span)}
                   for a in profile.assign],
    }


def model_to_raw(cfg: Config, model: dict, old_raw: dict | None = None) -> dict:
    """Edit-Modell -> kompakte Konfigurationsform (wie man sie von Hand schreiben würde)."""
    old_grids = (old_raw or {}).get("grids") or {}
    raw: dict = {}
    if model.get("description"):
        raw["description"] = model["description"]
    grids = {}
    weights = model.get("weights") or {}
    for alias, (cols, rows) in (model.get("grids") or {}).items():
        if alias not in cfg.monitors:
            raise ConfigError("unknown_monitor", mon=alias, where="grids")
        cols, rows = int(cols), int(rows)
        if not (1 <= cols <= 12 and 1 <= rows <= 12):
            raise ConfigError("grid_range", cols=cols, rows=rows, mon=alias)
        spec = spec_from_model(cols, rows, weights.get(alias))
        default = cfg.monitors[alias].grid
        prev = old_grids.get(alias)
        if spec.same_as(default):
            continue                               # entspricht dem Monitor-Standard -> nicht speichern
        if prev is not None and GridSpec.parse(prev).same_as(spec):
            grids[alias] = prev                    # unverändert -> Schreibweise des Nutzers behalten
        else:
            grids[alias] = spec_to_raw(spec)
    if grids:
        raw["grids"] = grids
    assign = {}
    for a in model.get("assign") or []:
        span = [int(v) for v in a.get("span") or (1, 1)]
        sub = a.get("sub")
        if span == [1, 1] or sub is not None:
            assign[a["char"]] = f"{a['monitor']}:{slot_text(int(a['slot']), None if sub is None else int(sub))}"
        else:
            assign[a["char"]] = {"monitor": a["monitor"], "slot": int(a["slot"]), "span": span}
    if assign:
        raw["assign"] = assign
    if model.get("fill"):
        raw["fill"] = list(model["fill"])
    subgrids = {}
    old_sub = (old_raw or {}).get("subgrids") or {}
    for sg in model.get("subgrids") or []:
        key = f"{sg['monitor']}:{int(sg['slot'])}"
        cols, rows = (int(v) for v in sg["grid"])
        if not (1 <= cols <= 8 and 1 <= rows <= 8):
            raise ConfigError("grid_range", cols=cols, rows=rows, mon=key)
        spec = spec_from_model(cols, rows, sg.get("weights"))
        if key in old_sub and GridSpec.parse(old_sub[key]).same_as(spec):
            subgrids[key] = old_sub[key]
        else:
            subgrids[key] = spec_to_raw(spec)
    if subgrids:
        raw["subgrids"] = subgrids
    overflow = []
    ofl = model.get("overflow") or []
    for n, o in enumerate(ofl):
        sub = o.get("sub")
        cell = f"{o['monitor']}:{slot_text(int(o['slot']), None if sub is None else int(sub))}"
        mx = o.get("max")
        overflow.append({"cell": cell, "max": int(mx)} if mx and n < len(ofl) - 1 else cell)
    if overflow:
        raw["overflow"] = overflow
    if model.get("hotkey"):
        raw["hotkey"] = model["hotkey"]
    if model.get("stack_hotkeys"):
        raw["stack_hotkeys"] = {k: v for k, v in model["stack_hotkeys"].items() if v}
    sp = {}
    for k, v in (model.get("stack_previews") or {}).items():
        if not v or not v.get("mode"):
            continue
        entry = {"mode": v["mode"]}
        if v.get("edge", "bottom") != "bottom":
            entry["edge"] = v["edge"]
        if int(v.get("size") or 18) != 18:
            entry["size"] = int(v["size"])
        if v.get("show") == "eve":
            entry["show"] = "eve"
        sp[k] = entry
    if sp:
        raw["stack_previews"] = sp
    blocked = {}
    for b in model.get("blocked") or []:
        sub = b.get("sub")
        key = f"{b['monitor']}:{slot_text(int(b['slot']), None if sub is None else int(sub))}"
        label, match = (b.get("label") or "").strip(), (b.get("match") or "").strip()
        preview = b.get("preview") or ""
        if preview:
            entry = {"label": label} if label else {}
            entry["preview"] = preview
            if b.get("preview_show") == "eve":
                entry["show"] = "eve"
            blocked[key] = entry
        else:
            blocked[key] = {"label": label, "match": match} if match else label
    if blocked:
        raw["blocked"] = blocked
    if model.get("disabled"):
        raw["disabled_monitors"] = [a for a in cfg.monitors if a in model["disabled"]]
    if model.get("stack_overflow") is False:     # Standard ist an – nur das Abschalten speichern
        raw["stack_overflow"] = False
    if model.get("focus"):
        raw["focus"] = model["focus"]
    return raw


def profile_from_model(cfg: Config, name: str, model: dict) -> Profile:
    return parse_profile(name, model_to_raw(cfg, model, _load_doc(cfg.path)[0]
                                            .get("profiles", {}).get(name)), cfg.monitors)


def _load_doc(path: Path):
    """Lädt die Datei so, dass sie möglichst verlustfrei zurückgeschrieben werden kann.

    Mit ruamel.yaml bleiben Kommentare und Formatierung erhalten; ohne fällt es auf
    PyYAML zurück (Kommentare gehen dann verloren – es wird eine .bak angelegt).
    Rückgabe: (doc, dumper)
    """
    text = path.read_text(encoding="utf-8")
    if not _is_yaml(path):
        return json.loads(text), lambda d: json.dumps(d, indent=2, ensure_ascii=False) + "\n"
    try:
        from io import StringIO

        from ruamel.yaml import YAML
        y = YAML()
        y.preserve_quotes = True
        y.width = 120
        y.default_flow_style = None   # kurze Listen wie [1, 2] inline schreiben

        def dump(d):
            buf = StringIO()
            y.dump(d, buf)
            return buf.getvalue()
        return y.load(text) or {}, dump
    except ImportError:
        yaml = _yaml()
        return (yaml.safe_load(text) or {},
                lambda d: yaml.safe_dump(d, sort_keys=False, allow_unicode=True, default_flow_style=None))


def _replace_key(mapping, old_key, new_key, value):
    """Setzt mapping[new_key] = value an der Position von old_key (Reihenfolge bleibt)."""
    if old_key in mapping and hasattr(mapping, "insert"):        # ruamel CommentedMap
        pos = list(mapping).index(old_key)
        del mapping[old_key]
        mapping.insert(pos, new_key, value)
        return mapping
    items = [(new_key if k == old_key else k, value if k == old_key else v) for k, v in mapping.items()]
    if old_key not in mapping:
        items.append((new_key, value))
    mapping.clear()
    mapping.update(items)
    return mapping


def _write_doc(path: Path, doc, dump) -> None:
    text = dump(doc)
    parse_text(text, path)                        # validieren, bevor etwas überschrieben wird
    bak = path.with_name(path.name + ".bak")
    bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    path.write_text(text, encoding="utf-8")


def save_profile(cfg: Config, name: str, model: dict, old_name: str | None = None) -> None:
    name = (name or "").strip()
    if not name:
        raise ConfigError("name_missing")
    doc, dump = _load_doc(cfg.path)
    if doc.get("profiles") is None:
        doc["profiles"] = {}
    profiles = doc["profiles"]
    if name != old_name and name in profiles:
        raise ConfigError("profile_exists", name=name)
    raw = model_to_raw(cfg, model, profiles.get(old_name or name))
    _replace_key(profiles, old_name if old_name in profiles else name, name, raw)
    if old_name and old_name != name and doc.get("default_profile") == old_name:
        doc["default_profile"] = name
    _write_doc(cfg.path, doc, dump)


def delete_profile(cfg: Config, name: str) -> None:
    doc, dump = _load_doc(cfg.path)
    profiles = doc.get("profiles") or {}
    if name not in profiles:
        raise ConfigError("unknown_profile", name=name)
    del profiles[name]
    if doc.get("default_profile") == name:
        doc["default_profile"] = next(iter(profiles), None)
        if doc["default_profile"] is None:
            del doc["default_profile"]
    _write_doc(cfg.path, doc, dump)


def set_default_profile(cfg: Config, name: str) -> None:
    if name not in cfg.profiles:
        raise ConfigError("unknown_profile", name=name)
    doc, dump = _load_doc(cfg.path)
    doc["default_profile"] = name
    _write_doc(cfg.path, doc, dump)


def save_settings(cfg: Config, hotkeys: dict | None = None, titlebar: dict | None = None,
                  characters: dict | None = None, separator: dict | None = None) -> None:
    """Globale Einstellungen aus der Web-UI zurückschreiben (nur die übergebenen Bereiche)."""
    doc, dump = _load_doc(cfg.path)
    if hotkeys is not None:
        hk = {k: v for k, v in hotkeys.items() if v}
        if hk:
            doc["hotkeys"] = hk
        elif "hotkeys" in doc:
            del doc["hotkeys"]
    if titlebar is not None:
        settings = doc.setdefault("settings", {})
        tb = {"hide": bool(titlebar.get("hide"))}
        if titlebar.get("color"):
            tb["color"] = str(titlebar["color"])
        if tb["hide"] or "color" in tb:
            settings["titlebar"] = tb
        elif "titlebar" in settings:
            del settings["titlebar"]
    if separator is not None:
        settings = doc.setdefault("settings", {})
        width = max(0, min(20, int(separator.get("width") or 0)))
        if width:
            settings["separator"] = {"width": width, "color": str(separator.get("color") or "#3c3c3c")}
            if separator.get("show") == "eve":
                settings["separator"]["show"] = "eve"
        elif "separator" in settings:
            del settings["separator"]
    if characters is not None:
        chars = {k: {"color": v["color"]} for k, v in characters.items() if v and v.get("color")}
        if chars:
            doc["characters"] = chars
        elif "characters" in doc:
            del doc["characters"]
    _write_doc(cfg.path, doc, dump)
