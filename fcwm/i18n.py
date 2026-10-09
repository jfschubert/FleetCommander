"""Mini-i18n für Server- und CLI-Meldungen (DE/EN).

Die aktive Sprache steckt in einer ContextVar: die Web-UI setzt sie pro Request
(Header X-Lang), die CLI einmalig aus settings.language bzw. $LANG.
"""
from __future__ import annotations

import os
from contextvars import ContextVar

LANGUAGES = ("de", "en")

MESSAGES: dict[str, dict[str, str]] = {
    # Layout / Plan
    "monitor_missing": {"de": "Monitor '{alias}' ({ref}) nicht angeschlossen – übersprungen",
                        "en": "Monitor '{alias}' ({ref}) not connected – skipped"},
    "monitor_unavailable": {"de": "{char}: Monitor '{mon}' nicht verfügbar",
                            "en": "{char}: monitor '{mon}' not available"},
    "monitor_disabled": {"de": "{char}: Monitor '{mon}' ist in diesem Profil deaktiviert – wird aufgefüllt",
                         "en": "{char}: monitor '{mon}' is disabled in this profile – filled elsewhere"},
    "no_subgrid": {"de": "Slot {slot} hat kein Subgrid", "en": "Slot {slot} has no subgrid"},
    "invalid_preview": {"de": "Ungültiger Vorschau-Modus '{value}' (all oder hidden)",
                        "en": "Invalid preview mode '{value}' (all or hidden)"},
    "cell_blocked": {"de": "{char}: Slot {slot} ist als frei gehalten markiert",
                     "en": "{char}: slot {slot} is marked as kept free"},
    "invalid_regex": {"de": "Ungültiges Fenster-Muster '{value}': {error}",
                      "en": "Invalid window pattern '{value}': {error}"},
    "too_small": {"de": "{char}: Slot {slot} ({w}x{h}) ist kleiner als das EVE-Minimum {mw}x{mh}",
                  "en": "{char}: slot {slot} ({w}x{h}) is smaller than the EVE minimum {mw}x{mh}"},
    "slot_missing": {"de": "Slot {slot} existiert nicht (Raster {cols}x{rows})",
                     "en": "Slot {slot} does not exist (grid {cols}x{rows})"},
    "span_outside": {"de": "Span {c}x{r} ab Slot {slot} ragt aus dem Raster",
                     "en": "Span {c}x{r} from slot {slot} extends beyond the grid"},
    # Konfiguration
    "no_monitors": {"de": "Keine Monitore in der Konfiguration definiert",
                    "en": "No monitors defined in the configuration"},
    "unknown_monitor": {"de": "Unbekannter Monitor '{mon}' ({where})",
                        "en": "Unknown monitor '{mon}' ({where})"},
    "invalid_assign": {"de": "Zuweisung für '{char}' ungültig: {value}",
                       "en": "Invalid assignment for '{char}': {value}"},
    "invalid_grid": {"de": "Ungültige Grid-Angabe: {value}", "en": "Invalid grid value: {value}"},
    "grid_range": {"de": "Raster {cols}x{rows} für '{mon}' ausserhalb 1..12",
                   "en": "Grid {cols}x{rows} for '{mon}' outside 1..12"},
    "unknown_profile": {"de": "Unbekanntes Profil: '{name}'", "en": "Unknown profile: '{name}'"},
    "profile_exists": {"de": "Profil '{name}' existiert bereits", "en": "Profile '{name}' already exists"},
    "name_missing": {"de": "Profilname fehlt", "en": "Profile name missing"},
    "default_missing": {"de": "default_profile '{name}' existiert nicht",
                        "en": "default_profile '{name}' does not exist"},
    "yaml_missing": {"de": "PyYAML fehlt (pip install pyyaml) – oder config.json verwenden",
                     "en": "PyYAML missing (pip install pyyaml) – or use config.json"},
    "no_config": {"de": "Keine Konfiguration gefunden (gesucht: {paths}). Mit `fcwm init` eine anlegen.",
                  "en": "No configuration found (searched: {paths}). Create one with `fcwm init`."},
    "init_done": {"de": "Konfiguration angelegt: {path}\nWeiter: `fcwm web` starten oder den Dienst aktivieren: "
                        "systemctl --user enable --now fcwm",
                  "en": "Configuration created: {path}\nNext: run `fcwm web` or enable the service: "
                        "systemctl --user enable --now fcwm"},
    "init_exists": {"de": "{path} existiert bereits (mit --force überschreiben)",
                    "en": "{path} already exists (use --force to overwrite)"},
    "reloaded": {"de": "Konfiguration neu geladen: {path}", "en": "Configuration reloaded: {path}"},
    "restarting": {"de": "Starte neu …", "en": "Restarting …"},
    "restarted_service": {"de": "Dienst fcwm neu gestartet.", "en": "fcwm service restarted."},
    "restarted_process": {"de": "fcwm neu gestartet.", "en": "fcwm restarted."},
    "not_running": {"de": "fcwm läuft nicht (weder Dienst noch `fcwm web`). Starten mit: "
                          "systemctl --user start fcwm",
                    "en": "fcwm is not running (neither service nor `fcwm web`). Start it with: "
                          "systemctl --user start fcwm"},
    "cleanup_service": {"de": "Der Dienst fcwm läuft noch – zuerst: systemctl --user disable --now fcwm",
                        "en": "The fcwm service is still running – first: systemctl --user disable --now fcwm"},
    "cleanup_done": {"de": "Aufgeräumt: {scripts} KWin-Skripte entladen, {shortcuts} Kurzbefehle und "
                           "{rules} Fensterregeln entfernt, Farbschemata gelöscht. Die Konfiguration bleibt erhalten.",
                     "en": "Cleaned up: {scripts} KWin scripts unloaded, {shortcuts} shortcuts and {rules} window "
                           "rules removed, color schemes deleted. Your configuration is kept."},
    # Backends
    "kwin_no_reply": {"de": "Keine Antwort vom KWin-Skript (journalctl). Läuft KWin mit Journal-Logging?",
                      "en": "No reply from the KWin script (journalctl). Is KWin logging to the journal?"},
    "windows_gone": {"de": "{n} Fenster nicht mehr vorhanden", "en": "{n} window(s) no longer exist"},
    "no_backend": {"de": "Kein passendes Backend gefunden (angefragt: {name})",
                   "en": "No suitable backend found (requested: {name})"},
    "wayland_no_kwin": {"de": "Wayland ohne erreichbares KWin – X11-Tools können hier keine Fenster verschieben",
                        "en": "Wayland without a reachable KWin – X11 tools cannot move windows here"},
    "no_monitors_detected": {"de": "Keine Monitore erkannt. {errors}", "en": "No monitors detected. {errors}"},
    # CLI / Logs
    "profile": {"de": "Profil", "en": "Profile"},
    "dry_run": {"de": "(Testlauf – nichts verschoben)", "en": "(dry run – nothing moved)"},
    "grid_area": {"de": "Raster {cols}x{rows}, Fläche {area}", "en": "grid {cols}x{rows}, area {area}"},
    "not_open": {"de": "(nicht eingeloggt)", "en": "(not logged in)"},
    "no_slot": {"de": "(kein Slot frei)", "en": "(no free slot)"},
    "warning": {"de": "WARNUNG", "en": "WARNING"},
    "focus": {"de": "Fokus", "en": "Focus"},
    "workarea": {"de": "Arbeitsbereich", "en": "work area"},
    "error": {"de": "Fehler", "en": "Error"},
    "listening": {"de": "Listener aktiv ({kind}) – Auto-Platzierung: {state}, Profil {profile}",
                  "en": "Listener active ({kind}) – auto placement: {state}, profile {profile}"},
    "placed": {"de": "Platziert: {char} → {slot}", "en": "Placed: {char} → {slot}"},
    "logged_in": {"de": "Neuer Client: {char}", "en": "New client: {char}"},
    "closed": {"de": "Client geschlossen: {char}", "en": "Client closed: {char}"},
    "on": {"de": "an", "en": "on"},
    "off": {"de": "aus", "en": "off"},
    "hk_next": {"de": "Nächstes Layout", "en": "Next layout"},
    "hk_prev": {"de": "Vorheriges Layout", "en": "Previous layout"},
    "hk_cycle": {"de": "Aktiven Stapel durchschalten", "en": "Cycle active stack"},
    "hk_profile": {"de": "Layout „{name}“", "en": "Layout “{name}”"},
    "hk_stack": {"de": "Stapel {cell} durchschalten ({profile})", "en": "Cycle stack {cell} ({profile})"},
    "web_url": {"de": "Web-UI: {url}", "en": "Web UI: {url}"},
}

_default = "de" if os.environ.get("LANG", "").lower().startswith("de") else "en"
current: ContextVar[str | None] = ContextVar("fcwm_lang", default=None)


def set_default(lang: str | None) -> None:
    global _default
    if lang in LANGUAGES:
        _default = lang


def lang() -> str:
    return current.get() or _default


def norm(lang: str | None) -> str:
    lang = (lang or "").lower()[:2]
    return lang if lang in LANGUAGES else _default


def t(key: str, **kw) -> str:
    entry = MESSAGES.get(key)
    if not entry:
        return key
    return entry.get(lang(), entry["en"]).format(**kw)


class FcwmError(Exception):
    """Fehler mit übersetzbarer Meldung; die Übersetzung passiert beim Erzeugen."""

    def __init__(self, key: str, **kw):
        self.key, self.kw = key, kw
        super().__init__(t(key, **kw))


class ConfigError(FcwmError, ValueError):
    pass
