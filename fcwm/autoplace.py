"""Listener + auto-placement of new EVE clients.

Flow: the backend reports window events (KWin signals or polling). A client
counts as "newly logged in" as soon as its title contains a character name – at startup
the window is just called "EVE", and only after character selection "EVE - Name".

If several clients log in in quick succession, the debounce collects them and
places them together (one plan, one KWin call). Clients that are already placed
are left alone and keep their slot (keep_ids).

Other windows: if auto-placement is on and the active profile has window cells (match or
catch_all), newly opened windows are collected the same way and put into their cell. Because many
programs only set their title shortly after opening, a new window is reassigned on title changes
for FRESH seconds; after that the tool no longer touches it.

State (on/off, profile) lives in fcwm-state.json next to the configuration.
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
FRESH = 10.0   # seconds during which a new window is reassigned on title change


def _short(text: str) -> str:
    return hashlib.sha1(text.encode()).hexdigest()[:8]


class AutoPlacer:
    def __init__(self, app, debounce: float = 1.0, max_wait: float = 4.0):
        self.app = app
        self.debounce, self.max_wait = debounce, max_wait
        self.state_path: Path = app.cfg.path.with_name("fcwm-state.json")
        st = self._load_state()
        self.enabled: bool = bool(st.get("auto_place", False))
        self.profile: str | None = st.get("auto_profile")   # active profile (auto-placement, shortcuts)
        self.lock: bool = bool(st.get("lock", False))
        self.locks: dict[str, list[int]] = {}    # window ID -> locked rectangle
        self.reload = threading.Event()          # load the KWin control script with new values
        self.overlay = SeparatorOverlay() if "lock" in app.backend.listener_features else None
        self.previews = PreviewOverlay() if self.overlay else None
        self.last_plan = None
        self._seen: dict[str, str] = {}          # window id -> char
        self._pending: set[str] = set()
        self._pending_extra: set[str] = set()    # new other windows (for window cells)
        self._fresh: dict[str, float] = {}       # window id -> time of opening
        self._first_pending = 0.0
        self._timer: threading.Timer | None = None
        self._mutex = threading.Lock()
        self._subscribers: list[queue.Queue] = []
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.history: list[dict] = []            # recent events for newly connected UIs

    # -- State ----------------------------------------------------------------
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
            # Turning on locks the clients where they currently are
            self.locks = {w.id: w.geometry.as_list() for w in self.app.clients().values()} if self.lock else {}
            self.reload.set()
        if profile is not ...:
            if profile and profile not in self.app.cfg.profiles:
                self.app.resolve_profile(profile)  # raises a translated error
            self.profile = profile or None
        st = self._load_state()
        st.update(auto_place=self.enabled, auto_profile=self.profile, lock=self.lock)
        self.reload.set()   # stack shortcuts depend on the active profile
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

    # -- Event distribution (Server-Sent Events) ---------------------------------
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
            try:   # show lines/preview for the active layout (clients are usually already in the right place)
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
            except Exception as e:  # noqa: BLE001 – restart listener
                log.error("Listener: %s", e)
                self.publish({"type": "error", "message": str(e)})
                self._stop.wait(3)

    # -- Control: shortcuts, locking (used by the KWin listener) -----------------
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
            except Exception as e:  # noqa: BLE001 – shortcuts must not stop the listener
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
        """After a complete apply: remember the active profile and update the locks."""
        if profile and profile in self.app.cfg.profiles and profile != self.profile:
            self.configure(profile=profile)
        if self.lock:
            self.locks = {p.window.id: p.rect.as_list() for p in plan.placements}
        self.reload.set()
        self.update_separators(plan)
        self.update_previews()

    def refresh(self) -> None:
        """After reloading the configuration: rebuild the control script (shortcuts, locking) and overlays
        (separators, preview) for the active layout – without moving windows."""
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
        """(Re)load preview cells for the last applied plan – the tiles themselves
        update continuously in KWin; reloading is only needed when cells/colors change."""
        if self.previews:
            try:
                self.previews.show(self.app.cfg, self.last_plan)
            except Exception as e:  # noqa: BLE001
                log.warning("Vorschau: %s", e)

    def update_separators(self, plan=None) -> None:
        """Draw lines for `plan`; without a plan, again for the last applied one (e.g. new color)."""
        if plan is not None:
            self.last_plan = plan
        plan = self.last_plan
        if self.overlay:
            try:
                self.overlay.show(self.app.cfg, plan)
            except Exception as e:  # noqa: BLE001
                log.warning("Trennlinien: %s", e)

    def reapply_active(self, delay: float = 0.0) -> None:
        """Re-apply the active layout – e.g. after title bars were hidden/shown
        (KWin keeps the inner size, the frame shrinks) or the gap has changed."""
        profile = self.effective_profile()
        if not profile:
            return
        if delay:
            time.sleep(delay)
        with self.app.lock:
            plan = self.app.apply(profile, focus=False)   # do not take focus away from anyone
        self.after_apply(plan, profile)

    def _wants_windows(self) -> bool:
        """Does the active profile have cells that take other windows (pattern or catch-all cell)?"""
        p = self.app.cfg.profiles.get(self.effective_profile() or "")
        return bool(p and any(b.match or b.catch_all for b in p.blocked))

    def _on_event(self, kind: str, w: Window) -> None:
        char = self.app.char_of(w)
        with self._mutex:
            if kind == "removed":
                if self.locks.pop(w.id, None) is not None:
                    self.reload.set()
                old = self._seen.pop(w.id, None)
                self._pending.discard(w.id)
                self._pending_extra.discard(w.id)
                self._fresh.pop(w.id, None)
                self.app.caught.discard(w.id)
                if old:
                    log.info(t("closed", char=old))
                    self.publish({"type": "closed", "char": old})
                return
            if not char:
                self._on_other(kind, w)
                return
            if self._seen.get(w.id) == char:
                return
            self._seen[w.id] = char
            log.info(t("logged_in", char=char))
            self.publish({"type": "login", "char": char, "auto": self.enabled})
            if self.enabled:
                if not self._pending:
                    self._first_pending = time.monotonic()
                self._pending.add(w.id)
                self._schedule()

    def _on_other(self, kind: str, w: Window) -> None:
        """Queue a new (or just-renamed new) non-EVE window for the window cells."""
        now = time.monotonic()
        self._fresh = {i: ts for i, ts in self._fresh.items() if now - ts <= FRESH}
        if kind == "added":
            self._fresh[w.id] = now
        if w.id not in self._fresh or w.transient or not self.enabled or not self._wants_windows():
            return
        if not self._pending and not self._pending_extra:
            self._first_pending = now
        self._pending_extra.add(w.id)
        self._schedule()

    def _schedule(self) -> None:
        if self._timer:
            self._timer.cancel()
        # Debounce, but place after max_wait at the latest
        delay = min(self.debounce, max(0.0, self._first_pending + self.max_wait - time.monotonic()))
        self._timer = threading.Timer(delay, self.flush)
        self._timer.daemon = True
        self._timer.start()

    def flush(self) -> None:
        with self._mutex:
            ids, self._pending = self._pending, set()
            xids, self._pending_extra = self._pending_extra, set()
        if not ids and not xids:
            return
        profile = self.effective_profile()
        try:
            with self.app.lock:
                windows, mons = self.app.snapshot()
                keep = {w.id for w in windows} - ids
                plan = make_plan(self.app.cfg, self.app.resolve_profile(profile), windows, mons,
                                 frame_geometry=self.app.backend.sets_frame_geometry, keep_ids=keep,
                                 catch_ids=self.app.caught | xids)
                moves = [p for p in plan.placements if p.window.id in ids]
                extra = [p for p in plan.extra if p.window.id in xids]
                self.app.caught = (self.app.caught - xids) | (set(plan.caught) & xids)
                if moves or extra:
                    self.app.backend.apply(moves + extra, raise_ids=plan.raise_order(ids))
                    self.update_separators(plan)
                    if self.lock and moves:
                        self.locks.update({p.window.id: p.rect.as_list() for p in moves})
                        self.reload.set()
            for p in moves:
                log.info(t("placed", char=p.char, slot=f"{p.monitor}:{slot_text(p.slot, p.sub)}"))
            for p in extra:
                log.info(t("placed", char=p.window.caption, slot=f"{p.monitor}:{slot_text(p.slot, p.sub)}"))
            if ids:
                new_chars = {self._seen.get(i) for i in ids}
                unplaced = [c for c in plan.unplaced if c in new_chars]
                self.publish({"type": "placed", "profile": profile,
                              "items": [{"char": p.char, "slot": f"{p.monitor}:{slot_text(p.slot, p.sub)}",
                                         "auto": p.auto} for p in moves],
                              "unplaced": unplaced})
            if extra:
                self.publish({"type": "windows", "profile": profile,
                              "items": [{"char": p.window.caption, "slot": f"{p.monitor}:{slot_text(p.slot, p.sub)}"}
                                        for p in extra]})
        except Exception as e:  # noqa: BLE001
            log.error("%s", e)
            self.publish({"type": "error", "message": str(e)})

    def place_existing(self) -> None:
        """Place all already open clients once (watch --initial)."""
        with self._mutex:
            self._pending |= set(self._seen)
            self._first_pending = time.monotonic()
        self.flush()


def run_forever(app, profile: str | None, initial: bool) -> None:
    """CLI `watch`: listener with auto-placement enabled."""
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
