"""KWin backend (Plasma 6, Wayland *and* X11).

How it works: Python generates a small KWin JavaScript, loads it via D-Bus
(org.kde.KWin /Scripting), runs it and unloads it again. The script writes
return values with print() to the systemd journal; we read them back there using
a unique marker.

D-Bus calls go through `busctl` (systemd) – Qt tools such as qdbus are not needed.
"""
from __future__ import annotations

import json
import logging
import os
import re
import select
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from collections.abc import Callable

from ..geometry import Rect
from ..monitors import Monitor
from .base import Backend, Placement, Window
from ..i18n import FcwmError

_JS_HELPERS = r"""
function _windows() {
    return workspace.windowList ? workspace.windowList() : workspace.clientList();
}
function _out(w) {
    if (w.output) return w.output.name;
    return null;
}
// Dialog/popup of another window (stays where the program opens it)
function _tr(w) {
    return !!(w.transient || w.modal);
}
"""

_JS_QUERY = r"""
_windows().forEach(function (w) {
    if (!w.normalWindow) return;
    var g = w.frameGeometry;
    print(M + "W " + JSON.stringify({
        id: w.internalId.toString(), caption: w.caption, cls: w.resourceClass,
        pid: w.pid, g: [g.x, g.y, g.width, g.height], out: _out(w), tr: _tr(w)
    }));
});
if (workspace.screens) {
    workspace.screens.forEach(function (s) {
        var a = workspace.clientArea(KWin.MaximizeArea, s, workspace.currentDesktop);
        var g = s.geometry;
        print(M + "S " + JSON.stringify({
            name: s.name, geo: [g.x, g.y, g.width, g.height],
            work: [a.x, a.y, a.width, a.height], scale: s.devicePixelRatio,
            manufacturer: s.manufacturer || "", model: s.model || "", serial: s.serialNumber || ""
        }));
    });
}
print(M + "END");
"""

_JS_APPLY = r"""
var byId = {};
_windows().forEach(function (w) { byId[w.internalId.toString()] = w; });
PLAN.forEach(function (p) {
    var w = byId[p.id];
    if (!w) { print(M + "MISSING " + p.id); return; }
    if (w.minimized) w.minimized = false;
    if (w.fullScreen) w.fullScreen = false;
    if (w.setMaximize) w.setMaximize(false, false);
    w.frameGeometry = {x: p.r[0], y: p.r[1], width: p.r[2], height: p.r[3]};
});
RAISE.forEach(function (id) {
    var w = byId[id];
    if (!w) return;
    if (workspace.raiseWindow) workspace.raiseWindow(w);
    else if ("activeWindow" in workspace) workspace.activeWindow = w;
    else workspace.activeClient = w;
});
if (FOCUS && byId[FOCUS]) {
    if ("activeWindow" in workspace) workspace.activeWindow = byId[FOCUS];
    else workspace.activeClient = byId[FOCUS];
}
print(M + "END");
"""


# Stays loaded and reports new/renamed/closed windows to the journal immediately.
_JS_LISTEN = r"""
function info(w) {
    var g = w.frameGeometry;
    return JSON.stringify({
        id: w.internalId.toString(), caption: w.caption, cls: w.resourceClass,
        pid: w.pid, g: [g.x, g.y, g.width, g.height], out: _out(w), tr: _tr(w)
    });
}
function hook(w) {
    if (!w.normalWindow) return;
    w.captionChanged.connect(function () { print(M + "caption " + info(w)); });
}
_windows().forEach(hook);
(workspace.windowAdded || workspace.clientAdded).connect(function (w) {
    if (!w.normalWindow) return;
    hook(w);
    print(M + "added " + info(w));
});
(workspace.windowRemoved || workspace.clientRemoved).connect(function (w) {
    if (w.normalWindow) print(M + "removed " + info(w));
});
print(M + "ready");
"""
# Control in the same script: global shortcuts, cycling stacks, pinning windows.
# CTRL = {caption, cls, hotkeys: [{name, title, keys, action, rect?}], locks: [{id, r}]}
_JS_CONTROL = r"""
var EVE_CAP = new RegExp(CTRL.caption), EVE_CLS = CTRL.cls ? new RegExp(CTRL.cls) : null;
function isEve(w) {
    return w && w.normalWindow && EVE_CAP.test(w.caption) && (!EVE_CLS || EVE_CLS.test(w.resourceClass));
}
function sameRect(g, r) {
    return Math.abs(g.x - r[0]) < 3 && Math.abs(g.y - r[1]) < 3 && Math.abs(g.width - r[2]) < 3 && Math.abs(g.height - r[3]) < 3;
}
function activate(w) {
    if (workspace.raiseWindow) workspace.raiseWindow(w);
    if ("activeWindow" in workspace) workspace.activeWindow = w; else workspace.activeClient = w;
}
// Cycle stacks: bring the bottom window of the stack to the top -> all in turn.
// Stacks of EVE clients or of other windows (reserved areas); `eve` = which kind.
function cycle(rect, eve) {
    var order = workspace.stackingOrder || _windows();
    var members = order.filter(function (w) {
        return w.normalWindow && !w.minimized && (eve === undefined || isEve(w) === eve) && sameRect(w.frameGeometry, rect);
    });
    if (members.length) activate(members[0]);
}
CTRL.hotkeys.forEach(function (h) {
    registerShortcut(h.name, h.title, h.keys, function () {
        if (h.action == "cycle-active") {
            var a = workspace.activeWindow || workspace.activeClient;
            if (a && a.normalWindow) { var g = a.frameGeometry; cycle([g.x, g.y, g.width, g.height], isEve(a)); }
        } else if (h.action == "cycle-rect") {
            cycle(h.rect);
        } else {
            print(M + "hotkey " + JSON.stringify({action: h.action}));
        }
    });
});
// Pinning: after move/resize/maximize/tiling, immediately back to its place
var LOCK = {};
CTRL.locks.forEach(function (l) { LOCK[l.id] = l.r; });
function restore(w) {
    var r = LOCK[w.internalId.toString()];
    if (!r) return;
    if (w.fullScreen) w.fullScreen = false;
    if (w.setMaximize) w.setMaximize(false, false);
    if (!sameRect(w.frameGeometry, r)) w.frameGeometry = {x: r[0], y: r[1], width: r[2], height: r[3]};
}
function lockHook(w) {
    if (!LOCK[w.internalId.toString()]) return;
    ["interactiveMoveResizeFinished", "maximizedChanged", "quickTileModeChanged", "fullScreenChanged"].forEach(function (sig) {
        if (w[sig]) w[sig].connect(function () { restore(w); });
    });
}
_windows().forEach(lockHook);
"""
LISTENER_PLUGIN = "fcwm_listener"
log = logging.getLogger("fcwm")


def _window_from(d: dict) -> Window:
    return Window(d["id"], d["caption"], d["cls"], int(d["pid"]),
                  Rect(*(round(v) for v in d["g"])), d.get("out"), bool(d.get("tr")))


# Don't start via /Scripting/Script<id>: KWin assigns the ID as "number of loaded scripts".
# Once a second script is kept loaded (separators) and scripts get reloaded,
# a new ID can collide with an existing one – "run" would then hit the wrong script and
# the new one would never run. Scripting.start() reliably starts all loaded, not yet running scripts.
SCRIPT_LOCK = threading.Lock()


def start_loaded_scripts() -> None:
    _busctl("/Scripting", "org.kde.kwin.Scripting", "start")


def _stale_shortcuts() -> set[str]:
    """Shortcuts from earlier runs (fcwm-*, formerly evewm-*) still registered in kglobalaccel."""
    r = subprocess.run(["busctl", "--user", "call", "org.kde.KWin", "/component/kwin",
                        "org.kde.kglobalaccel.Component", "shortcutNames"], capture_output=True, text=True)
    return set(re.findall(r'"((?:fcwm|evewm)-[^"]+)"', r.stdout))


def kwin_available() -> bool:
    if not shutil.which("busctl"):
        return False
    r = subprocess.run(["busctl", "--user", "status", "org.kde.KWin"],
                       capture_output=True, text=True)
    return r.returncode == 0


def _busctl(*args: str) -> str:
    r = subprocess.run(["busctl", "--user", "call", "org.kde.KWin", *args],
                       capture_output=True, text=True, timeout=10)
    if r.returncode != 0:
        raise RuntimeError(f"busctl {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout.strip()


class KWinBackend(Backend):
    name = "kwin"
    sets_frame_geometry = True

    def __init__(self, timeout: float = 3.0):
        self.timeout = timeout

    # -- Script execution --------------------------------------------------
    @staticmethod
    def _load(body: str, consts: dict, marker: str, plugin: str) -> None:
        header = f"var M = {json.dumps(marker)};\n" + "".join(
            f"var {k} = {json.dumps(v, ensure_ascii=True)};\n" for k, v in consts.items())
        with tempfile.NamedTemporaryFile("w", suffix=".js", prefix="fcwm_", delete=False) as f:
            f.write(header + _JS_HELPERS + body)
            path = f.name
        try:
            with SCRIPT_LOCK:
                _busctl("/Scripting", "org.kde.kwin.Scripting", "loadScript", "ss", path, plugin)
                start_loaded_scripts()
        finally:
            os.unlink(path)  # KWin has already read the script on startup

    @staticmethod
    def _unload(plugin: str) -> None:
        try:
            _busctl("/Scripting", "org.kde.kwin.Scripting", "unloadScript", "s", plugin)
        except RuntimeError:
            pass

    def _run(self, body: str, consts: dict) -> list[str]:
        marker = f"FCWM_{uuid.uuid4().hex[:12]}:"
        plugin = "fcwm_" + marker[6:-1]
        since = int(time.time()) - 1
        try:
            self._load(body, consts, marker, plugin)
            return self._collect(marker, since)
        finally:
            self._unload(plugin)

    def _collect(self, marker: str, since: int) -> list[str]:
        deadline = time.monotonic() + self.timeout
        while True:
            log = subprocess.run(["journalctl", "--user", "-o", "cat", "--no-pager",
                                  "--since", f"@{since}"],
                                 capture_output=True, text=True).stdout
            lines = [ln[ln.index(marker) + len(marker):] for ln in log.splitlines() if marker in ln]
            if "END" in lines:
                return lines
            if time.monotonic() > deadline:
                raise FcwmError("kwin_no_reply")
            time.sleep(0.05)

    # -- API ----------------------------------------------------------------
    def _query(self) -> tuple[list[Window], list[Monitor]]:
        wins, mons = [], []
        for ln in self._run(_JS_QUERY, {}):
            kind, _, payload = ln.partition(" ")
            if kind == "W":
                wins.append(_window_from(json.loads(payload)))
            elif kind == "S":
                d = json.loads(payload)
                mons.append(Monitor(d["name"], Rect(*(round(v) for v in d["geo"])),
                                    scale=float(d.get("scale") or 1),
                                    workarea=Rect(*(round(v) for v in d["work"])),
                                    manufacturer=d.get("manufacturer", ""), model=d.get("model", ""),
                                    serial=d.get("serial", "")))
        return wins, mons

    def list_windows(self) -> list[Window]:
        return self._query()[0]

    def screens(self) -> list[Monitor] | None:
        return self.snapshot()[1]

    def snapshot(self):
        wins, mons = self._query()
        return wins, sorted(mons, key=lambda m: (m.geometry.x, m.geometry.y)) or None

    listener_kind = "kwin-signals"

    listener_features = ("hotkeys", "lock")

    def listen(self, on_event: Callable[[str, Window], None], stop: threading.Event,
               interval: float = 30.0, control=None) -> None:
        """Event-driven: a permanently loaded KWin script reports window signals,
        and we follow the journal with `journalctl -f`. Every `interval` seconds we check
        whether the script is still loaded (e.g. after a KWin restart).

        `control` (optional) provides shortcuts/pins: control.consts() -> CTRL dict,
        control.reload (Event) -> reload the script with new values, control.on_hotkey(action)."""
        marker = f"FCWM_L{uuid.uuid4().hex[:10]}:"
        proc = subprocess.Popen(["journalctl", "--user", "-f", "-n", "0", "-o", "cat"],
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        try:
            time.sleep(0.3)  # journalctl must be reading before the script reports "ready"
            registered: list[str] = []

            def load():
                nonlocal registered
                self._unload(LISTENER_PLUGIN)
                consts, body = {}, _JS_LISTEN
                if control is not None:
                    ctrl = control.consts()
                    # so changed keys take effect: remove old entries in kglobalaccel
                    names = set(registered) | {h["name"] for h in ctrl["hotkeys"]} | _stale_shortcuts()
                    for name in names:
                        subprocess.run(["busctl", "--user", "call", "org.kde.kglobalaccel", "/kglobalaccel",
                                        "org.kde.KGlobalAccel", "unregister", "ss", "kwin", name],
                                       capture_output=True)
                    registered = [h["name"] for h in ctrl["hotkeys"]]
                    consts, body = {"CTRL": ctrl}, _JS_LISTEN + _JS_CONTROL
                self._load(body, consts, marker, LISTENER_PLUGIN)

            load()
            next_check = time.monotonic() + interval
            buf = b""
            while not stop.is_set():
                ready, _, _ = select.select([proc.stdout], [], [], 0.5)
                if ready:
                    chunk = os.read(proc.stdout.fileno(), 65536)
                    if not chunk:
                        raise RuntimeError("journalctl beendet")
                    buf += chunk
                    *lines, buf = buf.split(b"\n")
                    for raw in lines:
                        line = raw.decode("utf-8", "replace")
                        if marker not in line:
                            continue
                        kind, _, payload = line[line.index(marker) + len(marker):].partition(" ")
                        try:
                            if kind in ("added", "caption", "removed"):
                                on_event(kind, _window_from(json.loads(payload)))
                            elif kind == "hotkey" and control is not None:
                                control.on_hotkey(json.loads(payload)["action"])
                        except Exception:  # noqa: BLE001
                            log.exception("Listener-Callback fehlgeschlagen")
                if control is not None and control.reload.is_set():
                    control.reload.clear()
                    load()
                if time.monotonic() > next_check:
                    next_check = time.monotonic() + interval
                    loaded = _busctl("/Scripting", "org.kde.kwin.Scripting", "isScriptLoaded", "s",
                                     LISTENER_PLUGIN)
                    if not loaded.endswith("true"):
                        log.warning("KWin-Listener war entladen – lade neu")
                        load()
        finally:
            self._unload(LISTENER_PLUGIN)
            for name in registered:   # release shortcuts while the tool is not running
                subprocess.run(["busctl", "--user", "call", "org.kde.kglobalaccel", "/kglobalaccel",
                                "org.kde.KGlobalAccel", "unregister", "ss", "kwin", name], capture_output=True)
            proc.terminate()

    def apply(self, placements: list[Placement], focus: Window | None = None,
              raise_ids: list[str] | None = None) -> None:
        plan = [{"id": p.window.id, "r": p.rect.as_list()} for p in placements]
        lines = self._run(_JS_APPLY, {"PLAN": plan, "RAISE": raise_ids or [],
                                      "FOCUS": focus.id if focus else None})
        missing = [ln for ln in lines if ln.startswith("MISSING")]
        if missing:
            raise FcwmError("windows_gone", n=len(missing))
