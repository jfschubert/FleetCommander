"""Debug info for the web UI settings (and error reports)."""
from __future__ import annotations

import functools
import importlib.util
import os
import platform
import re
import shutil
import subprocess
import sys

from . import __version__


def _version_of(*cmd: str) -> str:
    """First version number from `<program> --version`, otherwise ""."""
    if not shutil.which(cmd[0]):
        return ""
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=5).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""
    m = re.search(r"\d+(?:\.\d+)+", out)
    return m.group(0) if m else ""


def _has_module(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except ModuleNotFoundError:   # parent package missing (e.g. "ruamel" for "ruamel.yaml")
        return False


@functools.cache
def static_info() -> dict:
    """Does not change at runtime – determine only once."""
    session = os.environ.get("XDG_SESSION_TYPE", "")
    return {
        "fcwm": __version__,
        "python": platform.python_version(),
        "kernel": platform.release(),
        "session": session or ("wayland" if os.environ.get("WAYLAND_DISPLAY") else "x11" if os.environ.get("DISPLAY") else ""),
        "desktop": os.environ.get("XDG_CURRENT_DESKTOP", ""),
        "kwin": _version_of("kwin_wayland", "--version") or _version_of("kwin_x11", "--version"),
        "plasma": _version_of("plasmashell", "--version"),
        "pyqt_webengine": _has_module("PyQt6.QtWebEngineWidgets"),
        "ruamel": _has_module("ruamel.yaml"),
        "executable": sys.executable,
    }


def info(app, placer, host: str, port: int) -> dict:
    status = placer.status()
    return {
        **static_info(),
        "backend": app.backend.name,
        "listener": status.get("listener", ""),
        "listener_running": bool(status.get("running")),
        "features": list(status.get("features") or []),
        "active_profile": status.get("effective_profile") or "",
        "config": str(app.cfg.path),
        "state_file": str(placer.state_path),
        "web": f"http://{host}:{port}/",
        "pid": os.getpid(),
    }
