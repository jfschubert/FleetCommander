"""Combines configuration, monitors and windows into a placement plan.

A spot is addressed by (monitor, slot, sub): sub is None for a normal grid cell
and the cell number if the slot has its own subgrid ("center:1.3").
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .appwindow import APP_ID
from .backends.base import Placement, Window
from .config import Config, Profile, parse_slot, slot_text
from .geometry import GridSpec, Rect, center_in, grid_cells, span_cells, strip_decoration
from .i18n import t
from .monitors import Monitor

Key = tuple[str, int, "int | None"]   # (monitor, slot, sub)


@dataclass
class MonitorLayout:
    alias: str
    monitor: Monitor
    area: Rect           # usable area after panel deduction and padding
    grid: GridSpec
    cells: list[Rect]
    subgrids: dict[int, tuple[GridSpec, list[Rect]]] = field(default_factory=dict)

    def rect(self, slot: int, sub: int | None = None, span: tuple[int, int] = (1, 1)) -> Rect:
        if sub is None:
            return span_cells(self.cells, self.grid, slot, span)
        if slot not in self.subgrids:
            raise ValueError(t("no_subgrid", slot=f"{self.alias}:{slot}"))
        grid, cells = self.subgrids[slot]
        return span_cells(cells, grid, sub)

    def keys(self) -> list[Key]:
        """All assignable spots in reading order; a slot with a subgrid is replaced by its cells."""
        out: list[Key] = []
        for i in range(self.grid.slot_count):
            if i in self.subgrids:
                out += [(self.alias, i, j) for j in range(self.subgrids[i][0].slot_count)]
            else:
                out.append((self.alias, i, None))
        return out

    def to_dict(self) -> dict:
        return {"alias": self.alias, "output": self.monitor.name,
                "geometry": self.monitor.geometry.as_list(), "area": self.area.as_list(),
                "grid": [self.grid.cols, self.grid.rows],
                "cells": [c.as_list() for c in self.cells],
                "subgrids": {str(i): {"grid": [g.cols, g.rows], "cells": [c.as_list() for c in cells]}
                             for i, (g, cells) in self.subgrids.items()}}


@dataclass
class Plan:
    profile: str
    layouts: dict[str, MonitorLayout]
    placements: list[Placement] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)     # in the profile, but no window open
    reserved: list[dict] = field(default_factory=list)   # slots of these missing characters
    disabled: list[str] = field(default_factory=list)    # monitors disabled in the profile
    blocked: list[dict] = field(default_factory=list)    # reserved cells
    overflow: list[dict] = field(default_factory=list)   # overflow cells (order, max, occupancy)
    stack_previews: list[dict] = field(default_factory=list)  # preview strips on stacks
    extra: list[Placement] = field(default_factory=list) # other windows (browser, RIFT) in reserved cells
    unplaced: list[str] = field(default_factory=list)    # window open, but no slot free
    caught: list[str] = field(default_factory=list)      # window IDs taken by the catch-all cell
    warnings: list[str] = field(default_factory=list)
    focus: Window | None = None

    def raise_order(self, only_ids: set[str] | None = None) -> list[str]:
        """Window IDs in the order in which they must be raised so that in
        each stack (several clients on the same spot) the first entry is on top."""
        stacks: dict[tuple, list[Placement]] = {}
        for p in self.placements:
            stacks.setdefault((p.monitor, p.slot, p.sub), []).append(p)
        for p in self.extra:      # window stacks in reserved cells (only equal-sized)
            stacks.setdefault(("extra", p.monitor, p.slot, p.sub, *p.rect.as_list()), []).append(p)
        order = []
        for members in stacks.values():
            if len(members) > 1:
                order += [p.window.id for p in reversed(members)
                          if only_ids is None or p.window.id in only_ids]
        return order

    def to_dict(self) -> dict:
        return {"profile": self.profile,
                "layouts": {k: v.to_dict() for k, v in self.layouts.items()},
                "placements": [{"char": p.char, "monitor": p.monitor, "slot": p.slot, "sub": p.sub,
                                "span": list(p.span), "auto": p.auto,
                                "window": p.window.to_dict(), "rect": p.rect.as_list()}
                               for p in self.placements],
                "missing": self.missing, "reserved": self.reserved, "disabled": self.disabled,
                "blocked": self.blocked, "overflow": self.overflow, "stack_previews": self.stack_previews,
                "extra": [{"window": p.window.to_dict(), "monitor": p.monitor, "slot": p.slot, "sub": p.sub,
                           "rect": p.rect.as_list()} for p in self.extra],
                "unplaced": self.unplaced, "warnings": self.warnings,
                "focus": self.focus.caption if self.focus else None}


def char_of(cfg: Config, w: Window) -> str | None:
    """Character name if `w` is a logged-in EVE client, otherwise None."""
    if cfg.class_re and not cfg.class_re.search(w.resource_class or ""):
        return None
    m = cfg.caption_re.search(w.caption)
    if not m:
        return None
    return (m.groupdict().get("char") or w.caption).strip() or None


def eve_like(cfg: Config, w: Window) -> bool:
    """EVE window, even before login (title just "EVE") – never ends up in a window cell."""
    if cfg.class_re:
        return bool(cfg.class_re.search(w.resource_class or ""))
    return bool(cfg.caption_re.search(w.caption)) or w.caption.strip() == "EVE"


def eve_windows(cfg: Config, windows: list[Window]) -> dict[str, Window]:
    """Filters EVE clients and returns {character name: window}."""
    found: dict[str, Window] = {}
    for w in windows:
        char = char_of(cfg, w)
        if char:
            found.setdefault(char, w)
    return found


def resolve_monitors(cfg: Config, detected: list[Monitor]) -> tuple[dict[str, Monitor], list[str]]:
    by_name = {m.name: m for m in detected}
    out, warnings = {}, []
    for alias, mc in cfg.monitors.items():
        mon = None
        if mc.output:
            mon = by_name.get(mc.output)
        elif mc.index is not None and 0 <= mc.index < len(detected):
            mon = detected[mc.index]
        if mon is None:
            warnings.append(t("monitor_missing", alias=alias, ref=mc.output or mc.index))
        else:
            out[alias] = mon
    return out, warnings


def build_layouts(cfg: Config, profile: Profile, monitors: dict[str, Monitor]) -> dict[str, MonitorLayout]:
    layouts = {}
    for alias, mon in monitors.items():
        if alias in profile.disabled:
            continue
        mc = cfg.monitors[alias]
        if mc.reserve == "auto":
            area = mon.workarea.intersect(mon.geometry) if mon.workarea else mon.geometry
        else:
            area = mc.reserve.apply(mon.geometry)
        area = mc.padding.apply(area)
        grid = profile.grids.get(alias, mc.grid)
        gap = cfg.effective_gap
        lay = MonitorLayout(alias, mon, area, grid, grid_cells(area, grid, gap))
        for (m, slot), sg in profile.subgrids.items():
            if m == alias and 0 <= slot < grid.slot_count:
                lay.subgrids[slot] = (sg, grid_cells(lay.cells[slot], sg, gap))
        layouts[alias] = lay
    return layouts


def make_plan(cfg: Config, profile_name: str | Profile, windows: list[Window], detected: list[Monitor],
              frame_geometry: bool = True, keep_ids: set[str] | None = None,
              catch_ids: set[str] | None = None) -> Plan:
    """keep_ids: windows that must not be moved. If they already sit on a
    free fill slot, they keep it – so nobody shifts when another client logs in
    (alphabetical order only applies to truly free spots).

    catch_ids: windows that a catch-all cell (catch_all) may take – newly opened or
    already caught ones. Existing windows are thus never swept up unasked."""
    profile = profile_name if isinstance(profile_name, Profile) else cfg.profiles[profile_name]
    profile_name = profile.name
    monitors, warnings = resolve_monitors(cfg, detected)
    layouts = build_layouts(cfg, profile, monitors)
    plan = Plan(profile_name, layouts, warnings=warnings)
    plan.disabled = [a for a in profile.disabled if a in monitors]

    clients = eve_windows(cfg, windows)
    lookup = {c.casefold(): c for c in clients}
    used: set[Key] = set()
    placed: set[str] = set()

    def label(alias: str, slot: int, sub: int | None) -> str:
        return f"{alias}:{slot_text(slot, sub)}"

    def final(rect: Rect) -> Rect:
        return rect if frame_geometry else strip_decoration(rect, cfg.decoration)

    def occupy(alias: str, slot: int, sub: int | None, span) -> Rect:
        lay = layouts[alias]
        rect = lay.rect(slot, sub, span)  # validates slot/sub/span
        if sub is not None:
            used.add((alias, slot, sub))
            return rect
        for r in range(span[1]):
            for c in range(span[0]):
                s_ = slot + r * lay.grid.cols + c
                used.add((alias, s_, None))
                if s_ in lay.subgrids:                     # whole cell occupied -> its subgrid too
                    used.update((alias, s_, j) for j in range(lay.subgrids[s_][0].slot_count))
        return rect

    def add(char: str, alias: str, slot: int, sub: int | None = None, span=(1, 1), auto=False,
            mark: bool = True):
        rect = occupy(alias, slot, sub, span) if mark else layouts[alias].rect(slot, sub, span)
        if rect.w < cfg.min_size[0] or rect.h < cfg.min_size[1]:
            plan.warnings.append(t("too_small", char=char, slot=label(alias, slot, sub), w=rect.w, h=rect.h,
                                   mw=cfg.min_size[0], mh=cfg.min_size[1]))
        plan.placements.append(Placement(clients[char], final(rect), f"{char}@{label(alias, slot, sub)}",
                                         char, alias, slot, tuple(span), auto, sub))
        placed.add(char)

    # 0) reserved cells: never for EVE clients; optionally place other windows there
    blocked: set[Key] = set()
    cells: list[tuple] = []       # (BlockedCell, Key, Rect) of the valid cells
    for b in profile.blocked:
        lay = layouts.get(b.monitor)
        if not lay:
            continue
        try:
            rect = lay.rect(b.slot, b.sub)
        except ValueError:
            continue
        key = (b.monitor, b.slot, b.sub)
        blocked.add(key)
        used.add(key)
        if b.sub is None and b.slot in lay.subgrids:
            used.update((b.monitor, b.slot, j) for j in range(lay.subgrids[b.slot][0].slot_count))
        cells.append((b, key, rect))

    taken_extra: set[str] = set()

    def candidate(w: Window) -> bool:
        # Dialogs/popups (transient) open where the program wants them
        return (w.id not in taken_extra and not w.transient and not eve_like(cfg, w)
                and not w.caption.startswith("fcwm-") and w.resource_class != APP_ID)

    def hit(rx: re.Pattern, w: Window) -> bool:
        return bool(rx.search(w.caption) or rx.search(w.resource_class or ""))

    found: dict[Key, list[Window]] = {}
    for b, key, _ in cells:       # cells with a pattern first – the catch-all cell only gets the rest
        if b.match:
            rx = re.compile(b.match, re.IGNORECASE)
            wins = [w for w in windows if candidate(w) and hit(rx, w)]
            found[key] = wins if b.stack else wins[:1]
            taken_extra.update(w.id for w in found[key])
    catch = next((c for c in cells if c[0].catch_all), None)
    if catch and catch_ids:
        b, key, _ = catch
        ex = re.compile(b.exclude, re.IGNORECASE) if b.exclude else None
        wins = [w for w in windows if w.id in catch_ids and candidate(w) and not (ex and hit(ex, w))]
        found[key] = found.get(key, []) + wins
        taken_extra.update(w.id for w in wins)
        plan.caught = [w.id for w in wins]

    for b, key, rect in cells:
        wins = found.get(key, [])
        for w in wins:
            name = w.caption if len(wins) > 1 or not b.label else b.label
            target = final(rect) if b.resize else center_in(final(rect), w.geometry)
            plan.extra.append(Placement(w, target, f"{name}@{label(*key)}", name,
                                        b.monitor, b.slot, (1, 1), False, b.sub))
        plan.blocked.append({"monitor": b.monitor, "slot": b.slot, "sub": b.sub, "label": b.label,
                             "match": b.match, "preview": b.preview, "preview_show": b.preview_show,
                             "stack": b.stack, "catch_all": b.catch_all, "resize": b.resize,
                             "exclude": b.exclude, "rect": rect.as_list(),
                             "window": wins[0].caption if wins else None,
                             "windows": [w.caption for w in wins]})

    # 1) fixed assignments from the profile
    for a in profile.assign:
        char = lookup.get(a.char.casefold())
        if a.monitor not in layouts:
            key = "monitor_disabled" if a.monitor in profile.disabled else "monitor_unavailable"
            plan.warnings.append(t(key, char=a.char, mon=a.monitor))
            continue
        try:
            if char is None:
                plan.missing.append(a.char)
                # reserve the spot anyway so that "fill" does not occupy it
                rect = occupy(a.monitor, a.slot, a.sub, a.span)
                plan.reserved.append({"char": a.char, "monitor": a.monitor, "slot": a.slot, "sub": a.sub,
                                      "span": list(a.span), "rect": rect.as_list()})
            else:
                add(char, a.monitor, a.slot, a.sub, a.span)
            if (a.monitor, a.slot, a.sub) in blocked:
                plan.warnings.append(t("cell_blocked", char=a.char, slot=label(a.monitor, a.slot, a.sub)))
        except ValueError as e:
            plan.warnings.append(f"{a.char}: {e}")

    # Determine overflow cells: they only take clients once all fill cells are occupied
    ofl: list[tuple[Key, int | None]] = []
    for o in profile.overflow:
        lay = layouts.get(o.monitor)
        key = (o.monitor, o.slot, o.sub)
        if not lay or key in blocked:
            continue
        try:
            lay.rect(o.slot, o.sub)
        except ValueError:
            continue
        ofl.append((key, o.max))
    ofl_keys = {k for k, _ in ofl}

    # 2) remaining clients (alphabetical) into free spots on the fill monitors
    fill_keys = [k for alias in profile.fill if alias in layouts for k in layouts[alias].keys()
                 if k not in ofl_keys]
    free = [k for k in fill_keys if k not in used]

    def near(a: Rect, b: Rect, tol: int = 8) -> bool:
        return all(abs(x - y) <= tol for x, y in zip(a.as_list(), b.as_list()))

    for char in sorted(c for c in clients if c not in placed and keep_ids
                       and clients[c].id in keep_ids):
        hit = next((k for k in free if near(final(layouts[k[0]].rect(k[1], k[2])), clients[char].geometry)), None)
        if hit:
            free.remove(hit)
            add(char, *hit, auto=True)

    for char in sorted(c for c in clients if c not in placed):
        if not free:
            plan.unplaced.append(char)
            continue
        add(char, *free.pop(0), auto=True)

    # 3a) fill overflow cells in order; the last one takes all the rest
    if ofl and plan.unplaced:
        count = {k: sum(1 for p in plan.placements if (p.monitor, p.slot, p.sub) == k) for k, _ in ofl}
        rest = []
        for char in plan.unplaced:
            for n, (k, mx) in enumerate(ofl):
                last = n == len(ofl) - 1
                if last or not mx or count[k] < mx:
                    add(char, *k, auto=True, mark=False)
                    count[k] += 1
                    break
            else:
                rest.append(char)
        plan.unplaced = rest
    for n, (k, mx) in enumerate(ofl):
        plan.overflow.append({"monitor": k[0], "slot": k[1], "sub": k[2], "order": n + 1,
                              "max": None if n == len(ofl) - 1 else mx,
                              "count": sum(1 for p in plan.placements if (p.monitor, p.slot, p.sub) == k),
                              "rect": layouts[k[0]].rect(k[1], k[2]).as_list()})

    # 3b) without overflow cells: stack what is left round-robin on the fill spots
    if profile.stack_overflow and plan.unplaced:
        targets = [k for k in fill_keys if k not in blocked]
        if targets:
            for n, char in enumerate(plan.unplaced):
                add(char, *targets[n % len(targets)], auto=True, mark=False)
            plan.unplaced = []

    # preview strips on stacks: strip along one edge of the cell
    for key, sp in profile.stack_previews.items():
        mon, _, slot_txt = key.partition(":")
        if mon not in layouts:
            continue
        try:
            main, sub = parse_slot(slot_txt)
            cell = final(layouts[mon].rect(main, sub))
        except ValueError:
            continue
        frac = sp["size"] / 100
        if sp["edge"] in ("bottom", "top"):
            h = max(40, round(cell.h * frac))
            strip = Rect(cell.x, cell.y + cell.h - h if sp["edge"] == "bottom" else cell.y, cell.w, h)
        else:
            w = max(60, round(cell.w * frac))
            strip = Rect(cell.x + cell.w - w if sp["edge"] == "right" else cell.x, cell.y, w, cell.h)
        plan.stack_previews.append({"key": key, "monitor": mon, "slot": main, "sub": sub, **sp,
                                    "rect": strip.as_list(), "stack": cell.as_list()})

    if profile.focus:
        fc = lookup.get(profile.focus.casefold())
        plan.focus = clients[fc] if fc else None
    return plan
