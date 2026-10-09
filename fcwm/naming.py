"""Monitor arrangement relative to the primary monitor – basis for automatic names.

Result per connector: row (top/middle/bottom or row1…, only with multiple rows), side
(left/right, center = the primary's column with multiple rows) and distance from the primary (only if
there is more than one column on that side). Examples:
  one row:     left-2 · left-1 · primary · right
  2x3:         top-left · top-center · top-right / bottom-left · bottom-center(★) · bottom-right
The web UI turns this into translated names; `fcwm init` uses the English short name as alias.
"""
from __future__ import annotations

from .monitors import Monitor


def _clusters(items: list[Monitor], start, length) -> list[list[Monitor]]:
    """Groups monitors whose ranges (x or y axis) overlap by more than half."""
    groups: list[list[Monitor]] = []
    for m in sorted(items, key=lambda m: start(m) + length(m) / 2):
        for g in groups:
            ref = g[0]
            overlap = min(start(m) + length(m), start(ref) + length(ref)) - max(start(m), start(ref))
            if overlap > 0.5 * min(length(m), length(ref)):
                g.append(m)
                break
        else:
            groups.append([m])
    return sorted(groups, key=lambda g: sum(start(m) + length(m) / 2 for m in g) / len(g))


def arrangement(monitors: list[Monitor]) -> dict[str, dict]:
    """{Anschluss: {"row": str|None, "side": str|None, "n": int|None, "primary": bool, "slug": str}}"""
    if not monitors:
        return {}
    rows = _clusters(monitors, lambda m: m.geometry.y, lambda m: m.geometry.h)
    cols = _clusters(monitors, lambda m: m.geometry.x, lambda m: m.geometry.w)
    row_of = {m.name: i for i, g in enumerate(rows) for m in g}
    col_of = {m.name: i for i, g in enumerate(cols) for m in g}
    primary = next((m for m in monitors if m.primary), None) \
        or min(monitors, key=lambda m: (m.geometry.x, m.geometry.y))   # fallback: leftmost/topmost
    pc = col_of[primary.name]
    left_cols = sum(1 for c in range(len(cols)) if c < pc)
    right_cols = sum(1 for c in range(len(cols)) if c > pc)
    nrows = len(rows)
    row_words = {1: [None], 2: ["top", "bottom"], 3: ["top", "middle", "bottom"]}.get(
        nrows, [f"row{i + 1}" for i in range(nrows)])
    out = {}
    for m in monitors:
        row = row_words[row_of[m.name]]
        dx = col_of[m.name] - pc
        if dx < 0:
            side, n = "left", (-dx if left_cols > 1 else None)
        elif dx > 0:
            side, n = "right", (dx if right_cols > 1 else None)
        else:
            side, n = ("center" if nrows > 1 and len(cols) > 1 else None), None
        is_primary = m.name == primary.name
        parts = [p for p in (row, side, str(n) if n else None) if p]
        slug = "primary" if is_primary and nrows == 1 else "-".join(parts) or "primary"
        out[m.name] = {"row": row, "side": side, "n": n, "primary": is_primary, "slug": slug}
    return out
