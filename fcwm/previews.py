"""Preview areas: live thumbnails of the EVE clients in a reserved area (like EVE-O Preview).

A KWin QML script creates a borderless window per preview area and shows a grid of
`WindowThumbnail`s in it – rendered by the compositor itself, without screen capture. Clicking a tile
activates the client. Mode "hidden" shows only clients that are currently covered (behind in the stack) or
minimized. Like the separators, such KWin windows always sit on top; they are therefore only
visible while an EVE client (or a window from a reserved area) is active.
"""
from __future__ import annotations

import json
import logging
import shutil
import tempfile
from pathlib import Path

from .backends.kwin import SCRIPT_LOCK, _busctl, start_loaded_scripts

log = logging.getLogger("fcwm")
PLUGIN = "fcwm_previews"

_QML = r"""
import QtQuick
import QtQuick.Window
import org.kde.kwin as KWinComponents

Item {
    id: root
    // in parentheses: otherwise "{}" would be an empty code block in QML instead of an object
    readonly property var cells: (CELLS)
    readonly property var colors: (COLORS)
    readonly property var extraIds: (EXTRA)
    readonly property var cap: new RegExp(CAPTION)
    readonly property var cls: CLS ? new RegExp(CLS) : null
    readonly property var aw: KWinComponents.Workspace.activeWindow
    property int rev: 0                      // tick for recomputation (stack, new clients, titles)

    function isEve(w) { return w && w.normalWindow && cap.test(w.caption) && (!cls || cls.test(w.resourceClass)); }
    // KWin's JS engine has no named group results -> take the first group
    function charOf(w) { var m = w.caption.match(cap); return m && m[1] ? m[1] : w.caption; }
    function same(a, b) {
        return Math.abs(a.x - b.x) < 3 && Math.abs(a.y - b.y) < 3 && Math.abs(a.width - b.width) < 3 && Math.abs(a.height - b.height) < 3;
    }
    function clients(mode, stack, tick) {
        var order = KWinComponents.Workspace.stackingOrder.filter(isEve);   // bottom -> top
        if (mode === "stack") {
            // only this stack: all members except the topmost visible one
            var members = order.filter(function (w) { return same(w.frameGeometry, {x: stack[0], y: stack[1], width: stack[2], height: stack[3]}); });
            var visible = members.filter(function (w) { return !w.minimized; });
            var top = visible.length ? visible[visible.length - 1] : null;
            return members.filter(function (w) { return w !== top; })
                          .sort(function (a, b) { return charOf(a).localeCompare(charOf(b)); });
        }
        var out = order.filter(function (w, i) {
            if (mode !== "hidden") return true;
            if (w.minimized) return true;
            for (var j = i + 1; j < order.length; j++)                      // is another client above?
                if (!order[j].minimized && same(order[j].frameGeometry, w.frameGeometry)) return true;
            return false;
        });
        return out.sort(function (a, b) { return charOf(a).localeCompare(charOf(b)); });
    }
    readonly property bool active: aw ? (isEve(aw) || extraIds.indexOf(aw.internalId.toString()) >= 0
                                         || aw.caption === "fcwm-preview") : false

    Timer { interval: 400; running: true; repeat: true; onTriggered: root.rev++ }

    Instantiator {
        model: root.cells
        delegate: Window {
            id: win
            readonly property var shown: root.clients(modelData.mode, modelData.stack, root.rev)
            readonly property int n: shown.length
            // pick the column count so the tiles (16:9) get as large as possible
            readonly property int cols: {
                var best = 1, bestArea = 0;
                for (var c = 1; c <= Math.max(1, n); c++) {
                    var r = Math.ceil(Math.max(1, n) / c);
                    var w = (width - 8 - (c - 1) * 4) / c, h = (height - 8 - (r - 1) * 4) / r;
                    var tw = Math.min(w, (h - 18) * 16 / 9);
                    if (tw > bestArea) { bestArea = tw; best = c; }
                }
                return best;
            }
            readonly property int rowsN: Math.max(1, Math.ceil(n / cols))
            flags: Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus | Qt.Tool
            x: modelData.rect[0]; y: modelData.rect[1]; width: modelData.rect[2]; height: modelData.rect[3]
            color: "#121212"
            title: "fcwm-preview"
            // "always" like EVE-O Preview; "eve" only while an EVE client is active.
            // Bars on stacks disappear when there is nothing to show (they would otherwise cover the game).
            visible: (modelData.show === "always" || root.active) && (!modelData.strip || n > 0)

            Text {
                visible: win.n === 0 && !modelData.strip
                anchors.centerIn: parent
                color: "#6a6a6a"; font.family: "DejaVu Sans Mono"; font.pixelSize: 13
                text: modelData.label || "Preview"
            }
            Grid {
                x: 4; y: 4
                columns: win.cols
                spacing: 4
                Repeater {
                    model: win.shown
                    delegate: Rectangle {
                        id: tile
                        readonly property var client: modelData
                        readonly property string name: root.charOf(client)
                        readonly property bool isActive: root.aw === client
                        width: (win.width - 8 - (win.cols - 1) * 4) / win.cols
                        height: (win.height - 8 - (win.rowsN - 1) * 4) / win.rowsN
                        color: "#000000"
                        border.width: isActive ? 2 : 1
                        border.color: isActive ? "#9fd3f2" : (root.colors[name] || "#3a3a3a")
                        KWinComponents.WindowThumbnail {
                            anchors.fill: parent; anchors.margins: 2; anchors.bottomMargin: 18
                            wId: tile.client.internalId
                        }
                        Rectangle {
                            anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom
                            anchors.margins: 1; height: 17
                            color: tile.isActive ? "#2e4a5e" : "#1c1c1c"
                            Rectangle { width: 3; height: parent.height; color: root.colors[tile.name] || "transparent" }
                            Text {
                                anchors.verticalCenter: parent.verticalCenter; x: 7
                                width: parent.width - 10; elide: Text.ElideRight
                                color: tile.isActive ? "#ffffff" : "#c9c9c9"
                                font.family: "DejaVu Sans Mono"; font.pixelSize: 11
                                text: tile.name + (tile.client.minimized ? "  (min)" : "")
                            }
                        }
                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                if (tile.client.minimized) tile.client.minimized = false;
                                KWinComponents.Workspace.raiseWindow(tile.client);
                                KWinComponents.Workspace.activeWindow = tile.client;
                            }
                        }
                    }
                }
            }
        }
    }
}
"""


class PreviewOverlay:
    def __init__(self):
        self._dir: Path | None = None
        self.available = bool(shutil.which("busctl"))

    def clear(self) -> None:
        _busctl("/Scripting", "org.kde.kwin.Scripting", "unloadScript", "s", PLUGIN)
        if self._dir:
            shutil.rmtree(self._dir, ignore_errors=True)
            self._dir = None

    def show(self, cfg, plan) -> int:
        """Show the plan's preview areas (or remove them). Returns: number of areas."""
        self.clear()
        if plan is None or not self.available:
            return 0
        cells = [{"rect": b["rect"], "mode": b["preview"], "label": b["label"], "show": b.get("preview_show", "always"),
                  "stack": None, "strip": False} for b in plan.blocked if b.get("preview")]
        cells += [{"rect": sp["rect"], "mode": sp["mode"], "label": "", "show": sp["show"],
                   "stack": sp["stack"], "strip": True} for sp in plan.stack_previews]
        if not cells:
            return 0
        colors = {c: v.get("color") for c, v in cfg.characters.items() if v.get("color")}
        qml = (_QML.replace("CELLS", json.dumps(cells))
                   .replace("COLORS", json.dumps(colors))
                   .replace("EXTRA", json.dumps([p.window.id for p in plan.extra]))
                   .replace("CAPTION", json.dumps(cfg.caption_re.pattern.replace("(?P<", "(?<")))
                   .replace("CLS", json.dumps(cfg.class_re.pattern if cfg.class_re else "")))
        self._dir = Path(tempfile.mkdtemp(prefix="fcwm-prv-"))   # KWin caches QML per path
        path = self._dir / "main.qml"
        path.write_text(qml, encoding="utf-8")
        with SCRIPT_LOCK:
            out = _busctl("/Scripting", "org.kde.kwin.Scripting", "loadDeclarativeScript", "ss", str(path), PLUGIN)
            if out.split()[-1:] and out.split()[-1].lstrip("-").isdigit() and int(out.split()[-1]) >= 0:
                start_loaded_scripts()
            else:
                log.warning("previews: KWin did not load the overlay (%s)", out)
        return len(cells)
