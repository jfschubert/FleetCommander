#!/usr/bin/env python3
"""Regenerate the web UI screenshots for the documentation.

    python3 website/screenshots/take.py

Starts an isolated fcwm web UI (x11 backend, port 8799) with demo-config.yaml in a temporary
directory, renders the pages offscreen with Qt WebEngine (needs PyQt6-WebEngine) in English and
German as the app window (with its window controls) and writes
website/static/img/screenshots/<name>-<lang>.png. Your own config and the
running fcwm service are not touched. The monitors are the ones connected to this machine.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "website" / "static" / "img" / "screenshots"
PORT = 8799
LANGS = ("en", "de")

# (name, JavaScript run on the page, wait in ms before the capture)
STEPS = [
    ("layout", "showPage('layout'); window.scrollTo(0, 0)", 1200),
    ("cell-menu", "showPage('layout'); document.querySelector('.cell .gear').click()", 900),
    ("fleet-fight", "closeMenu(); [...document.querySelectorAll('#tabs button')]"
                    ".find(b => b.textContent.includes('Fleet-Fight')).click()", 1500),
    ("settings", "showPage('settings'); window.scrollTo(0, 0)", 1000),
    ("about", "showPage('about'); window.scrollTo(0, 0)", 1000),
]


def capture(lang: str, demo_dir: str) -> None:
    """Runs in a child process (one QApplication per language)."""
    from PyQt6.QtCore import QSize, QTimer, QUrl
    from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWidgets import QApplication

    # show what a normal install looks like: ~/.config/fcwm and the default port
    tidy = r"""(() => { const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      while (w.nextNode()) { const n = w.currentNode;
        n.nodeValue = n.nodeValue.split(%r).join("~/.config/fcwm").split("127.0.0.1:%d").join("127.0.0.1:8765"); } })()""" % (demo_dir, PORT)

    # pretend to be the app window (fcwm app): a stub of its QWebChannel bridge makes the page show
    # its own window controls (minimize/maximize/close) as in the real frameless window
    bridge = r"""if (!window.fcwmApp) {
      const noop = () => {};
      window.fcwmApp = window.fcwmBridge = {maximizedChanged: {connect: noop}, isMaximized: (cb) => cb(false),
        minimize: noop, toggleMaximize: noop, close: noop, startMove: noop, startResize: noop, copyText: noop};
      window.dispatchEvent(new Event("fcwm-app"));
    }"""

    app = QApplication(sys.argv[:1])
    profile = QWebEngineProfile()   # off the record: no stored language/collapsed windows
    view = QWebEngineView()
    view.setPage(QWebEnginePage(profile, view))
    view.resize(QSize(1600, 1000))
    view.show()
    js = lambda code: view.page().runJavaScript(code, 0, lambda _r: None)   # noqa: E731
    steps = iter(STEPS)

    def nxt():
        step = next(steps, None)
        if step is None:
            app.quit()
            return
        name, code, wait = step
        js(bridge)
        js(code)
        QTimer.singleShot(wait - 200, lambda: js(tidy))
        QTimer.singleShot(wait, lambda: (view.grab().save(str(OUT / f"{name}-{lang}.png")), print(f"  {name}-{lang}.png"), nxt()))

    def start(_ok):
        view.loadFinished.disconnect(start)
        js(f"localStorage.setItem('fcwm.lang', '{lang}'); location.reload()")
        QTimer.singleShot(3000, nxt)

    view.loadFinished.connect(start)
    view.load(QUrl(f"http://127.0.0.1:{PORT}/"))
    QTimer.singleShot(60000, app.quit)
    app.exec()


def main() -> int:
    if len(sys.argv) == 4 and sys.argv[1] == "--capture":
        capture(sys.argv[2], sys.argv[3])
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="fcwm-shots-") as tmp:
        cfg = Path(tmp) / "config.yaml"
        shutil.copy(HERE / "demo-config.yaml", cfg)
        server = subprocess.Popen([sys.executable, "-m", "fcwm", "-b", "x11", "-c", str(cfg), "web", "--port", str(PORT)],
                                  cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            for _ in range(50):
                try:
                    urllib.request.urlopen(f"http://127.0.0.1:{PORT}/", timeout=1)
                    break
                except OSError:
                    time.sleep(0.2)
            # offscreen Qt needs software rendering, otherwise the captures stay black
            env = dict(os.environ, QT_QPA_PLATFORM="offscreen", QT_QUICK_BACKEND="software",
                       QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu --disable-gpu-compositing")
            for lang in LANGS:
                subprocess.run([sys.executable, __file__, "--capture", lang, tmp], env=env, check=True,
                               stderr=subprocess.DEVNULL)
        finally:
            server.terminate()
            server.wait()
    return 0


if __name__ == "__main__":
    sys.exit(main())
