"""Listener + Auto-Platzierung neuer EVE-Clients.

Ablauf: Das Backend meldet Fenster-Ereignisse (KWin-Signale bzw. Polling). Ein Client
zählt als "neu eingeloggt", sobald sein Titel einen Charakternamen enthält – beim Start
heisst das Fenster nur "EVE", erst nach der Charakterwahl "EVE - Name".

Werden mehrere Clients kurz nacheinander eingeloggt, sammelt der Debounce sie und
platziert sie gemeinsam (ein Plan, ein KWin-Aufruf). Bereits platzierte Clients werden
dabei nicht angefasst und behalten ihren Slot (keep_ids).

Zustand (an/aus, Profil) liegt in fcwm-state.json neben der Konfiguration.
"""
from __future__ import annotations

import hashlib
import json
import logging
import queue
import threading
import time
from pathlib import Path

from .backends import Window
from .config import parse_slot, slot_text
from .geometry import strip_decoration
from .previews import PreviewOverlay
from .separators import SeparatorOverlay
from .i18n import t
from .layout import make_plan

log = logging.getLogger("fcwm")


def _short(text: str) -> str:
    return hashlib.sha1(text.encode()).hexdigest()[:8]


class AutoPlacer:
    def __init__(self, app, debounce: float = 1.0, max_wait: float = 4.0):
        self.app = app
        self.debounce, self.max_wait = debounce, max_wait
        self.state_path: Path = app.cfg.path.with_name("fcwm-state.json")
        st = self._load_state()
        self.enabled: bool = bool(st.get("auto_place", False))
        self.profile: str | None = st.get("auto_profile")   # aktives Profil (Auto-Platzierung, Kurzbefehle)
        self.lock: bool = bool(st.get("lock", False))
        self.locks: dict[str, list[int]] = {}    # Fenster-ID -> fixiertes Rechteck
        self.reload = threading.Event()          # KWin-Steuerskript mit neuen Werten laden
        self.overlay = SeparatorOverlay() if "lock" in app.backend.listener_features else None
        self.previews = PreviewOverlay() if self.overlay else None
        self.last_plan = None
        self._seen: dict[str, str] = {}          # window id -> char
        self._pending: set[str] = set()
        self._first_pending = 0.0
        self._timer: threading.Timer | None = None
        self._mutex = threading.Lock()
        self._subscribers: list[queue.Queue] = []
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.history: list[dict] = []            # letzte Ereignisse für neu verbundene UIs

    # -- Zustand ----------------------------------------------------------------
    def _load_state(self) -> dict:
        try:
            return json.loads(self.state_path.read_text())
        except (OSError, ValueError):
            return {}

    def configure(self, enabled: bool | None = None, profile: str | None = ..., lock: bool | None = None) -> None:
        if enabled is not None:
            self.enabled = bool(enabled)
        if lock is not None and bool(lock) != self.lock:
            self.lock = bool(lock)
            # Einschalten fixiert die Clients dort, wo sie gerade sind
            self.locks = {w.id: w.geometry.as_list() for w in self.app.clients().values()} if self.lock else {}
            self.reload.set()
        if profile is not ...:
            if profile and profile not in self.app.cfg.profiles:
                self.app.resolve_profile(profile)  # wirft übersetzten Fehler
            self.profile = profile or None
        st = self._load_state()
        st.update(auto_place=self.enabled, auto_profile=self.profile, lock=self.lock)
        self.reload.set()   # Stapel-Kurzbefehle hängen am aktiven Profil
        self.state_path.write_text(json.dumps(st, indent=2))
        self.publish({"type": "auto", **self.status()})

    def status(self) -> dict:
        return {"enabled": self.enabled, "profile": self.profile,
                "effective_profile": self.effective_profile(),
                "listener": self.app.backend.listener_kind, "lock": self.lock,
                "features": list(self.app.backend.listener_features),
                "running": bool(self._thread and self._thread.is_alive())}

    def effective_profile(self) -> str | None:
        p = self.profile if self.profile in self.app.cfg.profiles else None
        return p or self.app.cfg.default_profile

    # -- Ereignis-Verteilung (Server-Sent Events) ---------------------------------
    def subscribe(self) -> queue.Queue:
        q: queue.Queue = queue.Queue(maxsize=200)
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: queue.Queue) -> None:
        if q in self._subscribers:
            self._subscribers.remove(q)

    def publish(self, event: dict) -> None:
        event = {"ts": time.time(), **event}
        if event["type"] != "auto":
            self.history = (self.history + [event])[-30:]
        for q in list(self._subscribers):
            try:
                q.put_nowait(event)
            except queue.Full:
                pass

    # -- Listener -------------------------------------------------------------------
    def start(self) -> None:
        clients = self.app.clients()
        self._seen = {w.id: c for c, w in clients.items()}
        self._thread = threading.Thread(target=self._run, name="fcwm-listener", daemon=True)
        self._thread.start()
        if self.overlay and self.effective_profile():
            try:   # Linien/Vorschau für das aktive Layout zeigen (Clients stehen meist schon richtig)
                self.update_separators(self.app.plan(self.effective_profile()))
                self.update_previews()
            except Exception as e:  # noqa: BLE001
                log.warning("Overlays: %s", e)
        log.info(t("listening", kind=self.app.backend.listener_kind,
                   state=t("on") if self.enabled else t("off"), profile=self.effective_profile()))

    def stop(self) -> None:
        if self.overlay:
            self.overlay.clear()
        if self.previews:
            self.previews.clear()
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=3)

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                self.app.backend.listen(self._on_event, self._stop, control=self)
            except Exception as e:  # noqa: BLE001 – Listener neu starten
                log.error("Listener: %s", e)
                self.publish({"type": "error", "message": str(e)})
                self._stop.wait(3)

    # -- Steuerung: Kurzbefehle, Fixieren (vom KWin-Listener genutzt) -----------------
    def consts(self) -> dict:
        cfg = self.app.cfg
        hotkeys = []

        def hk(name: str, title: str, keys: str, action: str, **extra):
            if keys:
                hotkeys.append({"name": name, "title": f"FleetCommander: {title}", "keys": keys, "action": action, **extra})

        h = cfg.hotkeys
        hk("fcwm-next-profile", t("hk_next"), h.get("next_profile", ""), "profile-next")
        hk("fcwm-prev-profile", t("hk_prev"), h.get("prev_profile", ""), "profile-prev")
        hk("fcwm-cycle-stack", t("hk_cycle"), h.get("cycle_stack", ""), "cycle-active")
        for name, p in cfg.profiles.items():
            hk("fcwm-profile-" + _short(name), t("hk_profile", name=name), p.hotkey, "profile:" + name)
        active = self.effective_profile()
        if active and cfg.profiles[active].stack_hotkeys:
            try:
                plan = self.app.plan(active, self.app.snapshot(max_age=5))
                for cell, keys in cfg.profiles[active].stack_hotkeys.items():
                    mon, _, slot = cell.partition(":")
                    main, sub = parse_slot(slot)
                    if mon in plan.layouts:
                        rect = plan.layouts[mon].rect(main, sub)
                        if not self.app.backend.sets_frame_geometry:
                            rect = strip_decoration(rect, cfg.decoration)
                        hk("fcwm-stack-" + _short(active + cell), t("hk_stack", cell=cell, profile=active),
                           keys, "cycle-rect", rect=rect.as_list())
            except Exception as e:  # noqa: BLE001 – Kurzbefehle sollen den Listener nicht stoppen
                log.warning("Stapel-Kurzbefehle: %s", e)
        return {"caption": cfg.caption_re.pattern.replace("(?P<", "(?<"),
                "cls": cfg.class_re.pattern if cfg.class_re else "",
                "hotkeys": hotkeys,
                "locks": [{"id": i, "r": r} for i, r in self.locks.items()] if self.lock else []}

    def on_hotkey(self, action: str) -> None:
        names = list(self.app.cfg.profiles)
        if not names:
            return
        cur = self.effective_profile()
        i = names.index(cur) if cur in names else 0
        if action == "profile-next":
            target = names[(i + 1) % len(names)]
        elif action == "profile-prev":
            target = names[(i - 1) % len(names)]
        elif action.startswith("profile:") and action[8:] in names:
            target = action[8:]
        else:
            return
        try:
            with self.app.lock:
                plan = self.app.apply(target)
            self.after_apply(plan, target)
            self.publish({"type": "profile", "name": target, "placed": len(plan.placements)})
        except Exception as e:  # noqa: BLE001
            self.publish({"type": "error", "message": str(e)})

    def after_apply(self, plan, profile: str | None = None) -> None:
        """Nach einem vollständigen Anwenden: aktives Profil merken und Fixierungen aktualisieren."""
        if profile and profile in self.app.cfg.profiles and profile != self.profile:
            self.configure(profile=profile)
        if self.lock:
            self.locks = {p.window.id: p.rect.as_list() for p in plan.placements}
        self.reload.set()
        self.update_separators(plan)
        self.update_previews()

    def refresh(self) -> None:
        """Nach dem Neuladen der Konfiguration: Steuerskript (Kurzbefehle, Fixieren) und Overlays
        (Trennlinien, Vorschau) für das aktive Layout neu aufbauen – ohne Fenster zu bewegen."""
        self.reload.set()
        profile = self.effective_profile()
        if self.overlay and profile:
            try:
                self.update_separators(self.app.plan(profile))
                self.update_previews()
            except Exception as e:  # noqa: BLE001
                log.warning("Overlays: %s", e)
        self.publish({"type": "auto", **self.status()})

    def update_previews(self) -> None:
        """Vorschau-Felder für den zuletzt angewendeten Plan (neu) laden – die Kacheln selbst
        aktualisieren sich in KWin laufend; neu laden ist nur bei geänderten Feldern/Farben nötig."""
        if self.previews:
            try:
                self.previews.show(self.app.cfg, self.last_plan)
            except Exception as e:  # noqa: BLE001
                log.warning("Vorschau: %s", e)

    def update_separators(self, plan=None) -> None:
        """Linien für `plan` zeichnen; ohne Plan erneut für den zuletzt angewendeten (z. B. neue Farbe)."""
        if plan is not None:
            self.last_plan = plan
        plan = self.last_plan
        if self.overlay:
            try:
                self.overlay.show(self.app.cfg, plan)
            except Exception as e:  # noqa: BLE001
                log.warning("Trennlinien: %s", e)

    def reapply_active(self, delay: float = 0.0) -> None:
        """Aktives Layout erneut anwenden – z. B. nachdem Titelleisten aus-/eingeblendet wurden
        (KWin behält die Innengrösse, der Rahmen schrumpft) oder sich der Abstand geändert hat."""
        profile = self.effective_profile()
        if not profile:
            return
        if delay:
            time.sleep(delay)
        with self.app.lock:
            plan = self.app.apply(profile, focus=False)   # niemandem den Fokus wegnehmen
        self.after_apply(plan, profile)

    def _on_event(self, kind: str, w: Window) -> None:
        char = self.app.char_of(w)
        with self._mutex:
            if kind == "removed":
                if self.locks.pop(w.id, None) is not None:
                    self.reload.set()
                old = self._seen.pop(w.id, None)
                self._pending.discard(w.id)
                if old:
                    log.info(t("closed", char=old))
                    self.publish({"type": "closed", "char": old})
                return
            if not char or self._seen.get(w.id) == char:
                return
            self._seen[w.id] = char
            log.info(t("logged_in", char=char))
            self.publish({"type": "login", "char": char, "auto": self.enabled})
            if self.enabled:
                if not self._pending:
                    self._first_pending = time.monotonic()
                self._pending.add(w.id)
                self._schedule()

    def _schedule(self) -> None:
        if self._timer:
            self._timer.cancel()
        # Debounce, aber spätestens nach max_wait platzieren
        delay = min(self.debounce, max(0.0, self._first_pending + self.max_wait - time.monotonic()))
        self._timer = threading.Timer(delay, self.flush)
        self._timer.daemon = True
        self._timer.start()

    def flush(self) -> None:
        with self._mutex:
            ids, self._pending = self._pending, set()
        if not ids:
            return
        profile = self.effective_profile()
        try:
            with self.app.lock:
                windows, mons = self.app.snapshot()
                keep = {w.id for w in windows} - ids
                plan = make_plan(self.app.cfg, self.app.resolve_profile(profile), windows, mons,
                                 frame_geometry=self.app.backend.sets_frame_geometry, keep_ids=keep)
                moves = [p for p in plan.placements if p.window.id in ids]
                if moves:
                    self.app.backend.apply(moves, raise_ids=plan.raise_order(ids))
                    self.update_separators(plan)
                    if self.lock:
                        self.locks.update({p.window.id: p.rect.as_list() for p in moves})
                        self.reload.set()
            for p in moves:
                log.info(t("placed", char=p.char, slot=f"{p.monitor}:{slot_text(p.slot, p.sub)}"))
            new_chars = {self._seen.get(i) for i in ids}
            unplaced = [c for c in plan.unplaced if c in new_chars]
            self.publish({"type": "placed", "profile": profile,
                          "items": [{"char": p.char, "slot": f"{p.monitor}:{slot_text(p.slot, p.sub)}", "auto": p.auto}
                                    for p in moves],
                          "unplaced": unplaced})
        except Exception as e:  # noqa: BLE001
            log.error("%s", e)
            self.publish({"type": "error", "message": str(e)})

    def place_existing(self) -> None:
        """Einmalig alle bereits offenen Clients platzieren (watch --initial)."""
        with self._mutex:
            self._pending |= set(self._seen)
            self._first_pending = time.monotonic()
        self.flush()


def run_forever(app, profile: str | None, initial: bool) -> None:
    """CLI `watch`: Listener mit eingeschalteter Auto-Platzierung."""
    placer = AutoPlacer(app)
    placer.enabled = True
    placer.profile = app.resolve_profile(profile)
    placer.start()
    if initial:
        placer.place_existing()
    try:
        while placer._thread.is_alive():
            placer._thread.join(1)
    finally:
        placer.stop()
