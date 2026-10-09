"""Separator lines between adjacent clients.

The grid leaves a gap of `separator.width` pixels between cells. A line is drawn
only where two windows actually abut – not at the edge, not next to empty
cells, and exactly one line per shared edge.

The lines are small, click-through KWin windows (QML script). KWin always puts such internal
windows on top. To make them behave like background anyway, the script hides
a line as soon as a window that sits ABOVE both neighbors in the stack covers the gap
(e.g. the focused window); likewise when there is no visible client on one side.
"""
from __future__ import annotations

import json
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from .backends.kwin import SCRIPT_LOCK, start_loaded_scripts
from .geometry import Rect

log = logging.getLogger("fcwm")
PLUGIN = "fcwm_separators"

_QML = r"""
import QtQuick
import QtQuick.Window
import org.kde.kwin as KWinComponents

Item {
    id: root
    readonly property var lines: (LINES)
    readonly property var extraIds: (EXTRA)
    readonly property bool always: SHOW_ALWAYS
    readonly property var aw: KWinComponents.Workspace.activeWindow
    readonly property var cap: new RegExp(CAPTION)
    readonly property var cls: CLS ? new RegExp(CLS) : null
    readonly property bool active: aw ? ((cap.test(aw.caption) && (!cls || cls.test(aw.resourceClass)))
                                         || extraIds.indexOf(aw.internalId.toString()) >= 0) : false
    property int rev: 0
    // Tick: immediately on stack/focus change, otherwise every 250 ms (e.g. while a window is being dragged)
    Timer { interval: 250; running: true; repeat: true; onTriggered: root.rev++ }
    Connections {
        target: KWinComponents.Workspace
        ignoreUnknownSignals: true
        function onStackingOrderChanged() { root.rev++ }
        function onWindowActivated() { root.rev++ }
        function onCurrentDesktopChanged() { root.rev++ }
    }
    function own(w) { return w.caption === "fcwm-separator" || w.caption === "fcwm-preview"; }
    function onCurrentDesktop(w) {
        try {
            if (w.onAllDesktops) return true;
            var cur = KWinComponents.Workspace.currentDesktop;
            return !w.desktops || w.desktops.length === 0 || w.desktops.indexOf(cur) >= 0;
        } catch (e) { return true; }
    }
    function shown(w) { return !w.minimized && !w.desktopWindow && !own(w) && onCurrentDesktop(w); }
    function sameRect(g, r) {
        return Math.abs(g.x - r[0]) < 3 && Math.abs(g.y - r[1]) < 3 && Math.abs(g.width - r[2]) < 3 && Math.abs(g.height - r[3]) < 3;
    }
    // Stack position of the topmost visible window on slot `r` (-1 = none)
    function topIndex(ws, r) {
        for (var i = ws.length - 1; i >= 0; i--)
            if (ws[i].normalWindow && shown(ws[i]) && sameRect(ws[i].frameGeometry, r)) return i;
        return -1;
    }
    // The line belongs to its two neighbors and sits on their level. It is only covered by
    // windows that sit ABOVE the neighbors in the stack (e.g. the focused window) – windows
    // behind them don't count. KWin always shows our overlays on top; this makes the line
    // behave as if it were in the background anyway.
    function lineVisible(m, tick) {
        if (!(always || active)) return false;
        var ws = KWinComponents.Workspace.stackingOrder;   // bottom -> top
        var ia = topIndex(ws, m.a), ib = topIndex(ws, m.b);
        if (ia < 0 || ib < 0) return false;                  // only between two visible windows
        var l = m.line;
        for (var k = Math.max(ia, ib) + 1; k < ws.length; k++) {
            var w = ws[k], g = w.frameGeometry;
            if (!shown(w) || sameRect(g, m.a) || sameRect(g, m.b)) continue;
            if (g.x < l[0] + l[2] && g.x + g.width > l[0] && g.y < l[1] + l[3] && g.y + g.height > l[1]) return false;
        }
        return true;
    }
    Instantiator {
        model: root.lines
        delegate: Window {
            flags: Qt.FramelessWindowHint | Qt.WindowTransparentForInput | Qt.WindowDoesNotAcceptFocus | Qt.Tool
            x: modelData.line[0]; y: modelData.line[1]; width: modelData.line[2]; height: modelData.line[3]
            color: COLOR
            title: "fcwm-separator"
            // only if there is a window on both sides and nothing else covers the gap
            visible: root.lineVisible(modelData, root.rev)
        }
    }
}
"""


def compute_lines(rects: list[Rect], gap: int) -> list[list[int]]:
    """Lines in the gaps between abutting rectangles (tolerance 1 px)."""
    return [line for line, _, _ in line_pairs(rects, gap)]


def line_pairs(rects: list[Rect], gap: int) -> list[tuple[list[int], list[int], list[int]]]:
    """Like compute_lines, additionally with the two adjacent rectangles per line."""
    if gap <= 0:
        return []
    uniq = list({r.as_list().__repr__(): r for r in rects}.values())
    found: dict[tuple, tuple] = {}
    for a in uniq:
        for b in uniq:
            if a is b:
                continue
            # b to the right of a
            if abs(b.x - (a.x + a.w + gap)) <= 1:
                top, bottom = max(a.y, b.y), min(a.y + a.h, b.y + b.h)
                if bottom - top > 0:
                    found.setdefault((a.x + a.w, top, b.x - (a.x + a.w), bottom - top), (a, b))
            # b below a
            if abs(b.y - (a.y + a.h + gap)) <= 1:
                left, right = max(a.x, b.x), min(a.x + a.w, b.x + b.w)
                if right - left > 0:
                    found.setdefault((left, a.y + a.h, right - left, b.y - (a.y + a.h)), (a, b))
    return [(list(l), a.as_list(), b.as_list()) for l, (a, b) in sorted(found.items())]


def _busctl(*args: str) -> str:
    return subprocess.run(["busctl", "--user", "call", "org.kde.KWin", *args],
                          capture_output=True, text=True).stdout.strip()


class SeparatorOverlay:
    def __init__(self):
        self._dir: Path | None = None
        self.available = bool(shutil.which("busctl"))

    def clear(self) -> None:
        _busctl("/Scripting", "org.kde.kwin.Scripting", "unloadScript", "s", PLUGIN)
        if self._dir:
            shutil.rmtree(self._dir, ignore_errors=True)
            self._dir = None

    def show(self, cfg, plan) -> int:
        """Show lines for the current plan (or remove them). Returns: number of lines."""
        self.clear()
        sep = cfg.separator or {}
        width = int(sep.get("width") or 0)
        if not width or plan is None or not self.available:
            return 0
        rects = [p.rect for p in plan.placements] + [p.rect for p in plan.extra]
        pairs = line_pairs(rects, cfg.effective_gap)
        if not pairs:
            return 0
        lines = [{"line": line, "a": a, "b": b} for line, a, b in pairs]
        qml = (_QML.replace("LINES", json.dumps(lines))
                   .replace("EXTRA", json.dumps([p.window.id for p in plan.extra]))
                   .replace("CAPTION", json.dumps(cfg.caption_re.pattern.replace("(?P<", "(?<")))
                   .replace("CLS", json.dumps(cfg.class_re.pattern if cfg.class_re else ""))
                   .replace("COLOR", json.dumps(sep.get("color") or "#3c3c3c"))
                   .replace("SHOW_ALWAYS", "false" if sep.get("show") == "eve" else "true"))
        # KWin remembers QML files per path -> a new directory every time
        self._dir = Path(tempfile.mkdtemp(prefix="fcwm-sep-"))
        path = self._dir / "main.qml"
        path.write_text(qml, encoding="utf-8")
        with SCRIPT_LOCK:
            out = _busctl("/Scripting", "org.kde.kwin.Scripting", "loadDeclarativeScript", "ss", str(path), PLUGIN)
            sid = out.split()[-1] if out else ""
            if sid.lstrip("-").isdigit() and int(sid) >= 0:
                start_loaded_scripts()   # don't start by script ID – see backends/kwin.py
            else:
                log.warning("separators: KWin did not load the overlay (%s)", out)
        return len(lines)
