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
    transient: bool = False     # belongs to another window (dialog/popup) – only KWin knows this

    def to_dict(self) -> dict:
        return {"id": self.id, "caption": self.caption, "class": self.resource_class,
                "pid": self.pid, "geometry": self.geometry.as_list(), "output": self.output,
                "transient": self.transient}


@dataclass
class Placement:
    window: Window
    rect: Rect          # target rectangle (frame geometry, i.e. including decoration)
    label: str = ""     # e.g. "Main@center:0" – for log output
    char: str = ""
    monitor: str = ""
    slot: int = 0
    span: tuple[int, int] = (1, 1)
    auto: bool = False  # True = distributed via "fill", not assigned explicitly
    sub: int | None = None  # cell in the subgrid of `slot`


class Backend(ABC):
    name = "base"
    # True if move() sets the frame rectangle (incl. title bar). Otherwise the
    # configured decoration is subtracted beforehand.
    sets_frame_geometry = True

    @abstractmethod
    def list_windows(self) -> list[Window]: ...

    @abstractmethod
    def apply(self, placements: list[Placement], focus: Window | None = None,
              raise_ids: list[str] | None = None) -> None:
        """Moves the windows; then raises `raise_ids` to the front in order
        (stacking order) and finally activates `focus`."""

    def screens(self) -> list[Monitor] | None:
        """Optional: monitors including work area (without panels). None = not supported."""
        return None

    # Listener ---------------------------------------------------------------
    # on_event(kind, window) with kind in {"added", "caption", "removed"}
    listener_kind = "polling"
    listener_features: tuple[str, ...] = ()   # e.g. ("hotkeys", "lock") – KWin only

    def listen(self, on_event: Callable[[str, Window], None], stop: threading.Event,
               interval: float = 2.0, control=None) -> None:
        """Blocks until `stop` is set. Default: compare the window list periodically."""
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
        """Windows and monitors in one go (backends can optimize this)."""
        return self.list_windows(), self.screens()
