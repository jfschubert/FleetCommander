"""Trennlinien zwischen benachbarten Clients.

Das Raster lässt zwischen den Zellen eine Lücke von `separator.width` Pixeln. Gezeichnet wird
nur dort, wo zwei Fenster tatsächlich aneinanderstossen – nicht am Rand, nicht neben leeren
Feldern, und pro gemeinsamer Kante genau eine Linie.

Die Linien sind kleine, klickdurchlässige KWin-Fenster (QML-Skript). KWin legt solche internen
Fenster immer ganz nach oben. Damit sie sich trotzdem wie Hintergrund verhalten, blendet das Skript
eine Linie aus, sobald ein Fenster, das im Stapel ÜBER den beiden Nachbarn liegt, die Lücke überdeckt
(z. B. das fokussierte Fenster); ebenso, wenn auf einer Seite kein sichtbarer Client steht.
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
    // Takt: sofort bei Stapel-/Fokuswechsel, sonst alle 250 ms (z. B. während ein Fenster gezogen wird)
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
    // Stapel-Position des obersten sichtbaren Fensters auf dem Platz `r` (-1 = keins)
    function topIndex(ws, r) {
        for (var i = ws.length - 1; i >= 0; i--)
            if (ws[i].normalWindow && shown(ws[i]) && sameRect(ws[i].frameGeometry, r)) return i;
        return -1;
    }
    // Die Linie gehört zu ihren beiden Nachbarn und liegt auf deren Ebene. Verdeckt wird sie nur von
    // Fenstern, die im Stapel ÜBER den Nachbarn liegen (z. B. das fokussierte Fenster) – Fenster
    // dahinter zählen nicht. KWin zeigt unsere Overlays immer zuoberst; so verhält sich die Linie
    // trotzdem, als läge sie im Hintergrund.
    function lineVisible(m, tick) {
        if (!(always || active)) return false;
        var ws = KWinComponents.Workspace.stackingOrder;   // unten -> oben
        var ia = topIndex(ws, m.a), ib = topIndex(ws, m.b);
        if (ia < 0 || ib < 0) return false;                  // nur zwischen zwei sichtbaren Fenstern
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
            // nur, wenn auf beiden Seiten ein Fenster steht und nichts anderes die Lücke überdeckt
            visible: root.lineVisible(modelData, root.rev)
        }
    }
}
"""


def compute_lines(rects: list[Rect], gap: int) -> list[list[int]]:
    """Linien in den Lücken zwischen aneinanderstossenden Rechtecken (Toleranz 1 px)."""
    return [line for line, _, _ in line_pairs(rects, gap)]


def line_pairs(rects: list[Rect], gap: int) -> list[tuple[list[int], list[int], list[int]]]:
    """Wie compute_lines, zusätzlich mit den beiden angrenzenden Rechtecken je Linie."""
    if gap <= 0:
        return []
    uniq = list({r.as_list().__repr__(): r for r in rects}.values())
    found: dict[tuple, tuple] = {}
    for a in uniq:
        for b in uniq:
            if a is b:
                continue
            # b rechts von a
            if abs(b.x - (a.x + a.w + gap)) <= 1:
                top, bottom = max(a.y, b.y), min(a.y + a.h, b.y + b.h)
                if bottom - top > 0:
                    found.setdefault((a.x + a.w, top, b.x - (a.x + a.w), bottom - top), (a, b))
            # b unter a
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
        """Linien für den aktuellen Plan anzeigen (bzw. entfernen). Rückgabe: Anzahl Linien."""
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
        # KWin merkt sich QML-Dateien pro Pfad -> jedes Mal ein neues Verzeichnis
        self._dir = Path(tempfile.mkdtemp(prefix="fcwm-sep-"))
        path = self._dir / "main.qml"
        path.write_text(qml, encoding="utf-8")
        with SCRIPT_LOCK:
            out = _busctl("/Scripting", "org.kde.kwin.Scripting", "loadDeclarativeScript", "ss", str(path), PLUGIN)
            sid = out.split()[-1] if out else ""
            if sid.lstrip("-").isdigit() and int(sid) >= 0:
                start_loaded_scripts()   # nicht per Skript-ID starten – siehe backends/kwin.py
            else:
                log.warning("Trennlinien: KWin hat das Overlay nicht geladen (%s)", out)
        return len(lines)
