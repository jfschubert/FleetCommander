"""X11 backend via wmctrl (list/move) with xdotool as fallback.

For X11 sessions without KWin, or as an alternative. Under Wayland this does
not work reliably (XWayland windows cannot be moved this way) – use the
KWin backend there.

Note: wmctrl -e usually sets the *client* geometry (without title bar);
so the layout code subtracts `settings.decoration` beforehand.
"""
from __future__ import annotations

import shutil
import subprocess

from ..geometry import Rect
from .base import Backend, Placement, Window


def _run(*cmd: str) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=10).stdout


class X11Backend(Backend):
    name = "x11"
    sets_frame_geometry = False

    def __init__(self):
        self.wmctrl = shutil.which("wmctrl")
        self.xdotool = shutil.which("xdotool")
        if not (self.wmctrl or self.xdotool):
            raise RuntimeError("Weder wmctrl noch xdotool gefunden")

    def list_windows(self) -> list[Window]:
        if self.wmctrl:
            return self._list_wmctrl()
        return self._list_xdotool()

    def _list_wmctrl(self) -> list[Window]:
        # Format: id desktop pid x y w h class host title...
        wins = []
        for line in _run("wmctrl", "-lpGx").splitlines():
            parts = line.split(None, 9)
            if len(parts) < 9 or parts[1] == "-1":  # -1 = sticky/panel
                continue
            wid, _, pid, x, y, w, h, cls = parts[:8]
            title = parts[9] if len(parts) > 9 else ""
            wins.append(Window(wid, title, cls.split(".")[-1], int(pid),
                               Rect(int(x), int(y), int(w), int(h))))
        return wins

    def _list_xdotool(self) -> list[Window]:
        wins = []
        # xdotool reports "nothing found" with exit code 1 – that is an empty list, not an error
        r = subprocess.run(["xdotool", "search", "--onlyvisible", "--name", "."],
                           capture_output=True, text=True, timeout=10)
        if r.returncode not in (0, 1):
            raise subprocess.CalledProcessError(r.returncode, r.args, r.stdout, r.stderr)
        ids = r.stdout.split()
        for wid in ids:
            try:
                title = _run("xdotool", "getwindowname", wid).strip()
                geo = dict(ln.split("=", 1) for ln in
                           _run("xdotool", "getwindowgeometry", "--shell", wid).split())
                pid = _run("xdotool", "getwindowpid", wid).strip() or "0"
            except subprocess.CalledProcessError:
                continue
            wins.append(Window(wid, title, "", int(pid),
                               Rect(int(geo["X"]), int(geo["Y"]), int(geo["WIDTH"]), int(geo["HEIGHT"]))))
        return wins

    def apply(self, placements: list[Placement], focus: Window | None = None,
              raise_ids: list[str] | None = None) -> None:
        for p in placements:
            r, wid = p.rect, p.window.id
            if self.wmctrl:
                subprocess.run(["wmctrl", "-i", "-r", wid, "-b",
                                "remove,maximized_vert,maximized_horz,fullscreen"], check=False)
                subprocess.run(["wmctrl", "-i", "-r", wid, "-e",
                                f"0,{r.x},{r.y},{r.w},{r.h}"], check=True)
            else:
                subprocess.run(["xdotool", "windowsize", wid, str(r.w), str(r.h),
                                "windowmove", wid, str(r.x), str(r.y)], check=True)
        for wid in raise_ids or []:
            if self.wmctrl:
                subprocess.run(["wmctrl", "-i", "-a", wid], check=False)
            else:
                subprocess.run(["xdotool", "windowraise", wid], check=False)
        if focus:
            if self.wmctrl:
                subprocess.run(["wmctrl", "-i", "-a", focus.id], check=False)
            else:
                subprocess.run(["xdotool", "windowactivate", focus.id], check=False)
