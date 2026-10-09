from __future__ import annotations

import os

from ..i18n import FcwmError
from .base import Backend, Placement, Window
from .kwin import KWinBackend, kwin_available
from .x11 import X11Backend

__all__ = ["Backend", "Placement", "Window", "get_backend"]


def get_backend(name: str = "auto") -> Backend:
    """auto: KWin if reachable (Wayland and X11), otherwise wmctrl/xdotool on X11."""
    if name == "kwin" or (name == "auto" and kwin_available()):
        return KWinBackend()
    if name == "x11" or (name == "auto" and os.environ.get("DISPLAY")):
        if name == "auto" and os.environ.get("WAYLAND_DISPLAY"):
            raise FcwmError("wayland_no_kwin")
        return X11Backend()
    raise FcwmError("no_backend", name=name)
