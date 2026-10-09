"""Anwendungsschicht – gemeinsam genutzt von CLI und Web-UI."""
from __future__ import annotations

import logging
import threading
import time

from . import config as config_mod
from .backends import Backend, Window, get_backend
from .config import Config, Profile
from .i18n import ConfigError
from .layout import Plan, char_of, eve_windows, make_plan
from .monitors import Monitor, detect_monitors

log = logging.getLogger("fcwm")


class App:
    def __init__(self, config_path: str | None = None, backend: str | None = None):
        self.cfg: Config = config_mod.load(config_path)
        self.backend: Backend = get_backend(backend or self.cfg.backend)
        self._snap = None
        self._snap_time = 0.0
        self.lock = threading.RLock()  # Backend-Aufrufe aus Web-Threads und Listener serialisieren

    def reload(self) -> None:
        self.cfg = config_mod.load(str(self.cfg.path))

    def save_config(self, text: str) -> None:
        """Validiert und speichert den Konfigurationstext (Web-Editor)."""
        config_mod.parse_text(text, self.cfg.path)  # wirft bei Fehlern
        self.cfg.path.write_text(text, encoding="utf-8")
        self.reload()

    def snapshot(self, max_age: float = 0.0) -> tuple[list[Window], list[Monitor]]:
        """Fenster + Monitore. KWin liefert zusätzlich den Arbeitsbereich ohne Panels;
        sonst kommen die Monitore von kscreen-doctor/xrandr.

        max_age > 0 erlaubt einen zwischengespeicherten Stand (Live-Vorschau im Editor)."""
        if self._snap and time.monotonic() - self._snap_time <= max_age:
            return self._snap
        windows, mons = self.backend.snapshot()
        self._snap = (windows, mons or detect_monitors())
        self._snap_time = time.monotonic()
        return self._snap

    def clients(self) -> dict[str, Window]:
        return eve_windows(self.cfg, self.snapshot()[0])

    def char_of(self, w: Window) -> str | None:
        return char_of(self.cfg, w)

    # -- Profil-Editor --------------------------------------------------------
    def draft(self, name: str, model: dict) -> Profile:
        return config_mod.profile_from_model(self.cfg, name or "Entwurf", model)

    def preview(self, name: str, model: dict) -> Plan:
        return make_plan(self.cfg, self.draft(name, model), *self.snapshot(max_age=60),
                         frame_geometry=self.backend.sets_frame_geometry)

    def save_profile(self, name: str, model: dict, old_name: str | None = None) -> None:
        config_mod.save_profile(self.cfg, name, model, old_name)
        self.reload()

    def delete_profile(self, name: str) -> None:
        config_mod.delete_profile(self.cfg, name)
        self.reload()

    def set_default(self, name: str) -> None:
        config_mod.set_default_profile(self.cfg, name)
        self.reload()

    def resolve_profile(self, profile: str | None) -> str:
        profile = profile or self.cfg.default_profile
        if not profile or profile not in self.cfg.profiles:
            raise ConfigError("unknown_profile", name=profile)
        return profile

    def plan(self, profile: str | Profile | None = None, snapshot=None) -> Plan:
        windows, mons = snapshot or self.snapshot()
        if not isinstance(profile, Profile):
            profile = self.resolve_profile(profile)
        return make_plan(self.cfg, profile, windows, mons,
                         frame_geometry=self.backend.sets_frame_geometry)

    def apply(self, profile: str | Profile | None = None, dry_run: bool = False,
              only_ids: set[str] | None = None, snapshot=None, focus: bool = True) -> Plan:
        plan = self.plan(profile, snapshot)
        placements = [p for p in plan.placements if only_ids is None or p.window.id in only_ids]
        if only_ids is None:
            placements += plan.extra
        if not dry_run and placements:
            self.backend.apply(placements, plan.focus if only_ids is None and focus else None,
                               plan.raise_order(only_ids))
        return plan

    def state(self) -> dict:
        windows, mons = self.snapshot()
        return {
            "monitor_config": {a: {"output": mc.output, "index": mc.index,
                                   "grid": [mc.grid.cols, mc.grid.rows],
                                   "weights": config_mod.weights_model(mc.grid)}
                               for a, mc in self.cfg.monitors.items()},
            "models": {n: config_mod.profile_to_model(self.cfg, p) for n, p in self.cfg.profiles.items()},
            "backend": self.backend.name,
            "config_path": str(self.cfg.path),
            "monitors": [m.to_dict() for m in mons],
            "clients": {c: w.to_dict() for c, w in eve_windows(self.cfg, windows).items()},
            # andere Fenster als Vorschläge für freigehaltene Felder (Browser, RIFT …)
            "windows": sorted({(w.caption, w.resource_class) for w in windows
                               if not char_of(self.cfg, w) and w.caption}),
            "profiles": {n: {"description": p.description} for n, p in self.cfg.profiles.items()},
            "default_profile": self.cfg.default_profile,
        }
