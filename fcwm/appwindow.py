"""Dedicated application window for the web UI (`fcwm app`) – for anyone who doesn't want a browser tab.

Simply shows the running web UI in a Qt WebEngine window (Chromium, as Plasma ships it
anyway). PyQt6-WebEngine is optional: if it is missing, the CLI opens the browser instead.

The window has no KDE title bar: the web UI's header bar serves as the title bar (static/js/
appframe.js). Via QWebChannel the page calls startSystemMove/-Resize here – the actual
moving is handled by KWin, also under Wayland. `native_frame=True` keeps the KDE title bar.
"""
from __future__ import annotations

from pathlib import Path

import sys
from urllib.parse import urlsplit

APP_ID = "fcwm"   # window class/Wayland app_id = name of the .desktop file (icon in the taskbar)
LOCAL_HOSTS = ("127.0.0.1", "localhost", "::1")


def is_internal(url: str) -> bool:
    """Stays in the window: the local web UI on any port (port change in the settings).
    Everything else is opened by the default browser."""
    u = urlsplit(url)
    return u.scheme in ("http", "https") and (u.hostname or "") in LOCAL_HOSTS


# Connects the page to the window: `window.fcwmBridge` (clipboard) always; with the custom frame also
# `window.fcwmApp` (window controls), announced via an event.
_BOOTSTRAP = """
new QWebChannel(qt.webChannelTransport, function (ch) {
    window.fcwmBridge = ch.objects.app;
    if (!%(native)s) {
        window.fcwmApp = ch.objects.app;
        window.dispatchEvent(new Event("fcwm-app"));
    }
});
"""


def run(url: str, native_frame: bool = False) -> int:
    """Open the window and block until it is closed. ImportError if PyQt6-WebEngine is missing."""
    from PyQt6.QtCore import QEvent, QFile, QIODevice, QObject, QSettings, Qt, QUrl, pyqtSignal, pyqtSlot
    from PyQt6.QtGui import QDesktopServices, QGuiApplication, QIcon, QKeySequence, QShortcut
    from PyQt6.QtWebChannel import QWebChannel
    from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineScript, QWebEngineSettings
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWidgets import QApplication, QMainWindow

    class Bridge(QObject):
        """Window functions for the web UI's header bar (names = JavaScript API)."""
        maximizedChanged = pyqtSignal(bool)

        def __init__(self, win):
            super().__init__()
            self._win = win

        @pyqtSlot()
        def startMove(self):   # noqa: N802 (JS API)
            if handle := self._win.windowHandle():
                handle.startSystemMove()

        @pyqtSlot(int)
        def startResize(self, edges):   # noqa: N802
            if handle := self._win.windowHandle():
                handle.startSystemResize(Qt.Edge(edges))

        @pyqtSlot()
        def minimize(self):
            self._win.showMinimized()

        @pyqtSlot()
        def toggleMaximize(self):   # noqa: N802
            self._win.showNormal() if self._win.isMaximized() else self._win.showMaximized()

        @pyqtSlot(result=bool)
        def isMaximized(self):   # noqa: N802
            return self._win.isMaximized()

        @pyqtSlot()
        def close(self):
            self._win.close()

        @pyqtSlot(str)
        def copyText(self, text):   # noqa: N802 – WebEngine blocks the JS clipboard API by default
            QGuiApplication.clipboard().setText(text)

    class Window(QMainWindow):
        bridge: Bridge | None = None

        def changeEvent(self, ev):   # noqa: N802 (Qt API)
            if ev.type() == QEvent.Type.WindowStateChange and self.bridge:
                self.bridge.maximizedChanged.emit(self.isMaximized())
            super().changeEvent(ev)

    class ExternalPage(QWebEnginePage):
        """Target for links with target="_blank": opens the address in the default browser and disappears."""
        def acceptNavigationRequest(self, target, kind, main_frame):   # noqa: N802 (Qt API)
            QDesktopServices.openUrl(target)
            self.deleteLater()
            return False

    class Page(QWebEnginePage):
        def acceptNavigationRequest(self, target, kind, main_frame):   # noqa: N802 (Qt API)
            if is_internal(target.toString()):
                return True
            QDesktopServices.openUrl(target)
            return False

        def createWindow(self, kind):   # noqa: N802 (Qt API) – new windows/tabs go to the browser
            return ExternalPage(self.profile(), self)

    app = QApplication(sys.argv[:1])
    app.setApplicationName(APP_ID)
    app.setApplicationDisplayName("FleetCommander")
    app.setDesktopFileName(APP_ID)
    icon = Path(__file__).resolve().parent / "static" / "fcwm.svg"
    app.setWindowIcon(QIcon(str(icon)) if icon.is_file() else QIcon.fromTheme("fcwm"))

    # own persistent profile: language, selected page etc. (localStorage) are preserved
    profile = QWebEngineProfile(APP_ID)
    win = Window()
    view = QWebEngineView(win)
    page = Page(profile, view)
    view.setPage(page)
    page.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
    if not native_frame:
        win.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
    win.bridge = Bridge(win)
    channel = QWebChannel(page)
    channel.registerObject("app", win.bridge)
    page.setWebChannel(channel)
    api = QFile(":/qtwebchannel/qwebchannel.js")   # shipped with Qt
    api.open(QIODevice.OpenModeFlag.ReadOnly)
    script = QWebEngineScript()
    script.setName("fcwm-bridge")
    script.setSourceCode(bytes(api.readAll()).decode() + _BOOTSTRAP % {"native": "true" if native_frame else "false"})
    script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
    script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
    script.setRunsOnSubFrames(False)
    page.scripts().insert(script)
    win.setCentralWidget(view)
    view.titleChanged.connect(lambda title: win.setWindowTitle(title or "FleetCommander"))
    QShortcut(QKeySequence("F5"), win, view.reload)
    QShortcut(QKeySequence("Ctrl+R"), win, view.reload)

    settings = QSettings(APP_ID, "app")
    if not win.restoreGeometry(settings.value("geometry", b"")):
        win.resize(1600, 1000)
    app.aboutToQuit.connect(lambda: settings.setValue("geometry", win.saveGeometry()))

    view.load(QUrl(url))
    win.show()
    code = app.exec()
    del view, win   # release the page before the profile, otherwise WebEngine warns on exit
    del profile
    return code
