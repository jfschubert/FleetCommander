from __future__ import annotations

import logging
import threading
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass

from ..geometry import Rect
from ..monitors import Monitor


@dataclass
class Window:
    id: str
    caption: str
    resource_class: str
    pid: int
    geometry: Rect
    output: str | None = None

    def to_dict(self) -> dict:
        return {"id": self.id, "caption": self.caption, "class": self.resource_class,
                "pid": self.pid, "geometry": self.geometry.as_list(), "output": self.output}


@dataclass
class Placement:
    window: Window
    rect: Rect          # Ziel-Rechteck (Frame-Geometrie, also inkl. Dekoration)
    label: str = ""     # z. B. "Main@center:0" – für Logausgaben
    char: str = ""
    monitor: str = ""
    slot: int = 0
    span: tuple[int, int] = (1, 1)
    auto: bool = False  # True = per "fill" verteilt, nicht fest zugewiesen
    sub: int | None = None  # Zelle im Subgrid von `slot`


class Backend(ABC):
    name = "base"
    # True, wenn move() das Frame-Rechteck (inkl. Titelleiste) setzt. Sonst wird
    # vorher die konfigurierte Dekoration abgezogen.
    sets_frame_geometry = True

    @abstractmethod
    def list_windows(self) -> list[Window]: ...

    @abstractmethod
    def apply(self, placements: list[Placement], focus: Window | None = None,
              raise_ids: list[str] | None = None) -> None:
        """Verschiebt die Fenster; holt danach `raise_ids` der Reihe nach nach vorn
        (Stapel-Reihenfolge) und aktiviert zuletzt `focus`."""

    def screens(self) -> list[Monitor] | None:
        """Optional: Monitore inkl. Arbeitsbereich (ohne Panels). None = nicht unterstützt."""
        return None

    # Listener ---------------------------------------------------------------
    # on_event(kind, window) mit kind in {"added", "caption", "removed"}
    listener_kind = "polling"
    listener_features: tuple[str, ...] = ()   # z. B. ("hotkeys", "lock") – nur mit KWin

    def listen(self, on_event: Callable[[str, Window], None], stop: threading.Event,
               interval: float = 2.0, control=None) -> None:
        """Blockiert bis `stop` gesetzt ist. Standard: Fensterliste regelmässig vergleichen."""
        known: dict[str, Window] = {}
        first = True
        while first or not stop.wait(interval):
            try:
                cur = {w.id: w for w in self.list_windows()}
            except Exception as e:  # noqa: BLE001
                logging.getLogger("fcwm").warning("listen: %s", e)
                first = False
                continue
            if not first:
                for wid, w in cur.items():
                    if wid not in known:
                        on_event("added", w)
                    elif known[wid].caption != w.caption:
                        on_event("caption", w)
                for wid in known.keys() - cur.keys():
                    on_event("removed", known[wid])
            known, first = cur, False

    def snapshot(self) -> tuple[list[Window], list[Monitor] | None]:
        """Fenster und Monitore in einem Rutsch (Backends können das optimieren)."""
        return self.list_windows(), self.screens()
