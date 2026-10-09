"""Web-UI auf Basis der Standardbibliothek (http.server).

Lauscht standardmässig nur auf 127.0.0.1 – die API kann Fenster verschieben und
die Konfiguration überschreiben, gehört also nicht ins Netzwerk.

Live-Ereignisse (neue Clients, Auto-Platzierung) gehen per Server-Sent Events an
/api/events.
"""
from __future__ import annotations

import json
import logging
import os
import queue
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import i18n
from .app import App
from . import config as config_mod
from . import titlebar
from .autoplace import AutoPlacer
from .i18n import t

log = logging.getLogger("fcwm.web")
STATIC = Path(__file__).parent / "static"


def serve(app: App, host: str = "127.0.0.1", port: int = 8765) -> None:
    placer = AutoPlacer(app)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            log.debug(fmt, *args)

        def setup(self):
            super().setup()
            i18n.current.set(i18n.norm(None))

        def _lang(self) -> None:
            i18n.current.set(i18n.norm(self.headers.get("X-Lang")))

        def _send(self, code: int, body: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, data, code: int = 200) -> None:
            self._send(code, json.dumps(data, ensure_ascii=False).encode(), "application/json")

        def _body(self) -> dict:
            n = int(self.headers.get("Content-Length") or 0)
            return json.loads(self.rfile.read(n) or b"{}")

        def do_GET(self):
            self._lang()
            path = self.path.split("?")[0]
            if path in ("/", "/index.html"):
                self._send(200, (STATIC / "index.html").read_bytes(), "text/html; charset=utf-8")
            elif path == "/api/state":
                try:
                    with app.lock:
                        st = app.state()
                    st["auto"] = placer.status()
                    st["settings"] = {"hotkeys": app.cfg.hotkeys, "titlebar": app.cfg.titlebar,
                                      "separator": app.cfg.separator,
                                      "characters": app.cfg.characters,
                                      "titlebar_available": titlebar.available()}
                    st["events"] = placer.history
                    self._json(st)
                except Exception as e:  # noqa: BLE001
                    self._json({"error": str(e)}, 500)
            elif path == "/api/config":
                self._send(200, app.cfg.path.read_bytes(), "text/plain; charset=utf-8")
            elif path == "/api/events":
                self._events()
            else:
                self._send(404, b"not found", "text/plain")

        def _events(self) -> None:
            q = placer.subscribe()
            try:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(b"retry: 2000\n\n")
                self.wfile.flush()
                while True:
                    try:
                        ev = q.get(timeout=15)
                        self.wfile.write(f"data: {json.dumps(ev, ensure_ascii=False)}\n\n".encode())
                    except queue.Empty:
                        self.wfile.write(b": ping\n\n")  # hält die Verbindung offen, erkennt Abbrüche
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                placer.unsubscribe(q)

        def do_POST(self):
            self._lang()
            # Schutz vor Cross-Site-Requests aus fremden Webseiten im Browser
            if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                return self._json({"error": "Content-Type application/json required"}, 415)
            try:
                data = self._body()
                with app.lock:
                    if self.path == "/api/apply":
                        # mit "model" wird ein (ungespeicherter) Entwurf angewendet
                        profile = (app.draft(data.get("name"), data["model"]) if data.get("model")
                                   else data.get("profile"))
                        plan = app.apply(profile, dry_run=bool(data.get("dry_run")))
                        if not data.get("dry_run"):
                            placer.after_apply(plan, data.get("profile") or data.get("name"))
                        return self._json(plan.to_dict())
                    if self.path == "/api/preview":
                        return self._json(app.preview(data.get("name"), data["model"]).to_dict())
                    if self.path == "/api/profile":
                        app.save_profile(data["name"], data["model"], data.get("old_name"))
                        if placer.profile == data.get("old_name") and data["name"] != data.get("old_name"):
                            placer.configure(profile=data["name"])
                        placer.reload.set()   # Profil-/Stapel-Kurzbefehle neu registrieren
                        return self._json({"ok": True})
                    if self.path == "/api/profile/delete":
                        app.delete_profile(data["name"])
                        if placer.profile == data["name"]:
                            placer.configure(profile=None)
                        placer.reload.set()
                        return self._json({"ok": True})
                    if self.path == "/api/default":
                        app.set_default(data["name"])
                        return self._json({"ok": True})
                    if self.path == "/api/config":
                        app.save_config(data["text"])
                        titlebar.sync(app.cfg)
                        placer.reload.set()
                        return self._json({"ok": True})
                    if self.path == "/api/settings":
                        old_hide, old_sep = bool(app.cfg.titlebar.get("hide")), dict(app.cfg.separator)
                        config_mod.save_settings(app.cfg, data.get("hotkeys"), data.get("titlebar"),
                                                 data.get("characters"), data.get("separator"))
                        app.reload()
                        if "titlebar" in data or "characters" in data:
                            titlebar.apply_rules(app.cfg)
                        placer.reload.set()
                        hide_changed = bool(app.cfg.titlebar.get("hide")) != old_hide
                        width_changed = app.cfg.separator.get("width") != old_sep.get("width")
                        if hide_changed or width_changed:
                            # ohne Titelleiste schrumpft der Rahmen bzw. die Lücke ändert sich ->
                            # Clients neu ausrichten; KWin braucht nach dem Neuladen der Regeln einen Moment
                            placer.reapply_active(delay=0.8 if hide_changed else 0.0)
                        elif app.cfg.separator != old_sep:
                            placer.update_separators()   # Farbe/Sichtbarkeit: Linien neu zeichnen, nichts bewegen
                        if "characters" in data:
                            placer.update_previews()     # Namensfarben in den Vorschau-Kacheln
                        return self._json({"ok": True})
                    if self.path == "/api/lock":
                        placer.configure(lock=bool(data.get("enabled")))
                        return self._json(placer.status())
                    if self.path == "/api/reload":
                        # Konfiguration neu einlesen (z. B. nach Handbearbeitung) – nichts wird verschoben
                        app.reload()
                        titlebar.sync(app.cfg)
                        placer.refresh()
                        log.info(t("reloaded", path=app.cfg.path))
                        return self._json({"ok": True, "config": str(app.cfg.path)})
                    if self.path == "/api/restart":
                        # sauber beenden (KWin-Skripte entladen, Kurzbefehle freigeben) und neu starten
                        restart.set()
                        threading.Thread(target=srv.shutdown, daemon=True).start()
                        return self._json({"ok": True, "pid": os.getpid()})
                    if self.path == "/api/auto":
                        placer.configure(data.get("enabled"), data.get("profile", ...))
                        return self._json(placer.status())
                self._json({"error": "unknown endpoint"}, 404)
            except Exception as e:  # noqa: BLE001
                self._json({"error": str(e)}, 400)

    restart = threading.Event()
    srv = ThreadingHTTPServer((host, port), Handler)
    srv.daemon_threads = True
    placer.start()
    try:
        titlebar.sync(app.cfg)   # z. B. nach Handbearbeitung der Konfiguration
    except Exception as e:  # noqa: BLE001
        log.warning("Titelleisten: %s", e)
    log.info(t("web_url", url=f"http://{host}:{port}/"))
    try:
        srv.serve_forever()
    finally:
        placer.stop()
        srv.server_close()
    if restart.is_set():
        # gleicher Prozess (gleiche PID, auch unter systemd), gleiche Argumente
        log.info(t("restarting"))
        os.execv(sys.executable, [sys.executable] + sys.orig_argv[1:])
