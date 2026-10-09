"""Reine Geometrie: Rechtecke, Abzüge (Panels/Ränder) und Raster-Berechnung.

Keine Abhängigkeit zu Backends – dadurch einfach testbar.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .i18n import ConfigError


@dataclass(frozen=True)
class Rect:
    x: int
    y: int
    w: int
    h: int

    def shrink(self, top: int = 0, right: int = 0, bottom: int = 0, left: int = 0) -> "Rect":
        return Rect(self.x + left, self.y + top,
                    max(0, self.w - left - right), max(0, self.h - top - bottom))

    def intersect(self, other: "Rect") -> "Rect":
        x1, y1 = max(self.x, other.x), max(self.y, other.y)
        x2 = min(self.x + self.w, other.x + other.w)
        y2 = min(self.y + self.h, other.y + other.h)
        return Rect(x1, y1, max(0, x2 - x1), max(0, y2 - y1))

    def as_list(self) -> list[int]:
        return [self.x, self.y, self.w, self.h]


@dataclass(frozen=True)
class Insets:
    """Abstände in Pixel (für Panel-Reservierung, Rand-Padding, Dekoration)."""
    top: int = 0
    right: int = 0
    bottom: int = 0
    left: int = 0

    @classmethod
    def parse(cls, value) -> "Insets":
        if value is None:
            return cls()
        if isinstance(value, (int, float)):
            v = int(value)
            return cls(v, v, v, v)
        if isinstance(value, dict):
            return cls(int(value.get("top", 0)), int(value.get("right", 0)),
                       int(value.get("bottom", 0)), int(value.get("left", 0)))
        raise ValueError(f"Ungültige Insets-Angabe: {value!r}")

    def apply(self, r: Rect) -> Rect:
        return r.shrink(self.top, self.right, self.bottom, self.left)


@dataclass(frozen=True)
class GridSpec:
    cols: int = 1
    rows: int = 1
    col_weights: tuple[float, ...] = field(default=())
    row_weights: tuple[float, ...] = field(default=())
    # eigene Spaltenaufteilung einzelner Zeilen: ((zeile, (gewichte…)), …) – z. B. Zeile 1 = 75:25
    row_col_weights: tuple[tuple[int, tuple[float, ...]], ...] = field(default=())

    def cols_for_row(self, row: int) -> tuple[float, ...]:
        return dict(self.row_col_weights).get(row, self.col_weights)

    @classmethod
    def parse(cls, value) -> "GridSpec":
        """Akzeptiert "2x2" (Spalten x Zeilen), [2, 2] oder ein Dict mit Gewichten."""
        if isinstance(value, GridSpec):
            return value
        if isinstance(value, str):
            c, r = value.lower().split("x")
            return cls(int(c), int(r))
        if isinstance(value, (list, tuple)) and len(value) == 2:
            return cls(int(value[0]), int(value[1]))
        if isinstance(value, dict):
            cols, rows = int(value.get("cols", 1)), int(value.get("rows", 1))
            per_row = tuple(sorted((int(r), tuple(float(x) for x in w))
                                   for r, w in (value.get("row_col_weights") or {}).items()
                                   if 0 <= int(r) < rows and w))
            spec = cls(cols, rows, tuple(value.get("col_weights", ()) or ()),
                       tuple(value.get("row_weights", ()) or ()), per_row)
            checks = [("col_weights", spec.col_weights, cols), ("row_weights", spec.row_weights, rows)]
            checks += [(f"row_col_weights[{r}]", w, cols) for r, w in per_row]
            for name, ws, n in checks:
                if ws and len(ws) != n:
                    raise ValueError(f"{name} braucht {n} Einträge, hat {len(ws)}")
            return spec
        raise ConfigError("invalid_grid", value=value)

    @property
    def slot_count(self) -> int:
        return self.cols * self.rows

    @staticmethod
    def _norm(weights: tuple[float, ...], n: int) -> tuple[float, ...]:
        weights = weights or (1.0,) * n
        total = float(sum(weights))
        return tuple(round(w / total, 4) for w in weights)

    def same_as(self, other: "GridSpec") -> bool:
        """Gleiches Raster, unabhängig davon, wie die Gewichte notiert sind ([2, 1] == [66.7, 33.3])."""
        return ((self.cols, self.rows) == (other.cols, other.rows)
                and all(self._norm(self.cols_for_row(r), self.cols) == self._norm(other.cols_for_row(r), other.cols)
                        for r in range(self.rows))
                and self._norm(self.row_weights, self.rows) == self._norm(other.row_weights, other.rows))

    @property
    def uniform(self) -> bool:
        return self.same_as(GridSpec(self.cols, self.rows))


def _edges(total: int, n: int, gap: int, weights: tuple[float, ...]) -> list[tuple[int, int]]:
    """Teilt `total` Pixel in n Segmente (Offset, Länge) mit `gap` dazwischen.

    Rundung über kumulierte Kanten, damit keine Pixel verloren gehen.
    """
    weights = weights or (1.0,) * n
    avail = max(0, total - gap * (n - 1))
    s = float(sum(weights))
    cum, acc = [0], 0.0
    for w in weights:
        acc += w
        cum.append(round(avail * acc / s))
    return [(cum[i] + i * gap, cum[i + 1] - cum[i]) for i in range(n)]


def grid_cells(area: Rect, grid: GridSpec, gap: int = 0) -> list[Rect]:
    """Alle Zellen eines Rasters, zeilenweise nummeriert (0 = oben links)."""
    rows = _edges(area.h, grid.rows, gap, grid.row_weights)
    out = []
    for r, (ry, rh) in enumerate(rows):   # jede Zeile kann ihre eigene Spaltenaufteilung haben
        out += [Rect(area.x + cx, area.y + ry, cw, rh)
                for (cx, cw) in _edges(area.w, grid.cols, gap, grid.cols_for_row(r))]
    return out


def span_cells(cells: list[Rect], grid: GridSpec, slot: int, span: tuple[int, int] = (1, 1)) -> Rect:
    """Rechteck, das ab `slot` über `span` = (Spalten, Zeilen) Zellen reicht."""
    if not 0 <= slot < grid.slot_count:
        raise ConfigError("slot_missing", slot=slot, cols=grid.cols, rows=grid.rows)
    c0, r0 = slot % grid.cols, slot // grid.cols
    sc, sr = span
    if c0 + sc > grid.cols or r0 + sr > grid.rows:
        raise ConfigError("span_outside", c=sc, r=sr, slot=slot)
    first = cells[r0 * grid.cols + c0]
    last = cells[(r0 + sr - 1) * grid.cols + (c0 + sc - 1)]
    return Rect(first.x, first.y, last.x + last.w - first.x, last.y + last.h - first.y)


def strip_decoration(frame: Rect, deco: Insets) -> Rect:
    """Frame-Rechteck -> Client-Rechteck (für Backends, die Client-Geometrie setzen)."""
    return deco.apply(frame)
