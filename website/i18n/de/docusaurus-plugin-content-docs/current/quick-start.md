---
sidebar_position: 3
title: Schnellstart & CLI
---

# Schnellstart & CLI-Referenz

## Erste Schritte

```bash
fcwm init                # Startkonfiguration aus deinen Monitoren (~/.config/fcwm/config.yaml)
fcwm monitors            # Anschlussnamen + Arbeitsbereich (ohne Panels)
fcwm windows             # erkannte EVE-Clients
fcwm apply -n            # Testlauf mit dem Standardprofil
fcwm apply Fleet-Fight   # Profil anwenden
fcwm watch Solo-Mining   # Listener: neue Clients beim Einloggen automatisch platzieren
fcwm watch --initial     # … und beim Start bereits offene Clients einmal platzieren
fcwm web                 # Web-UI auf http://127.0.0.1:8765/ (inkl. Listener)
fcwm --lang en apply -n  # Sprache der Ausgaben (de/en)
```

**Kurzbefehle ohne laufendes fcwm:** Systemeinstellungen → Tastatur → Kurzbefehle → *Neu hinzufügen* →
*Befehl*: `fcwm apply Fleet-Fight`. Läuft fcwm, lassen sich [globale Kurzbefehle](hotkeys-appearance.md)
auch direkt in der Web-UI festlegen.

**Autostart:** `systemctl --user enable --now fcwm` (siehe [Installation](installation.md)).

## Befehle

| Befehl | Beschreibung |
|---|---|
| `fcwm monitors` | Erkannte Monitore anzeigen (Geometrie, Skalierung, Arbeitsbereich). |
| `fcwm windows [--all]` | EVE-Clients anzeigen; `--all` listet alle Fenster mit Fensterklasse. |
| `fcwm profiles` | Profile auflisten (`*` markiert das Standardprofil). |
| `fcwm apply [PROFIL] [-n]` | Profil anwenden (Standard: `default_profile`); `-n`/`--dry-run` berechnet und zeigt nur. |
| `fcwm watch [PROFIL] [--initial]` | Auf neue Clients warten und automatisch platzieren. |
| `fcwm web [--host H] [--port N]` | Web-UI starten (inkl. Listener). |
| `fcwm open [--port N]` | Web-UI im Browser öffnen (startet fcwm bei Bedarf). |
| `fcwm app [--port N] [--native-frame]` | Web-UI in einem eigenen [Programmfenster](web-ui.md#app-window) öffnen (startet fcwm bei Bedarf; ohne PyQt6-WebEngine stattdessen im Browser). |
| `fcwm reload [--port N]` | Laufende Instanz liest die Konfiguration neu (verschiebt nichts). |
| `fcwm restart [--port N]` | Laufende Instanz neu starten (systemd-Dienst oder von Hand gestartetes `fcwm web`). |
| `fcwm state` | Gesamten Zustand als JSON ausgeben. |
| `fcwm init [--force]` | Startkonfiguration aus den erkannten Monitoren anlegen. |
| `fcwm cleanup` | Von fcwm angelegte KWin-Skripte, Kurzbefehle, Fensterregeln und Farbschemata entfernen (vor dem Deinstallieren). |

`fcwm web` lauscht auf `settings.web.host` / `settings.web.port` aus der Konfiguration (Standard
`127.0.0.1:8765`); `--host` und `--port` überschreiben das. `open`, `reload` und `restart` verwenden den
eingestellten Port, wenn `--port` fehlt. Siehe [Adresse der Web-UI](configuration.md#web-ui-address).

### Globale Optionen

| Option | Beschreibung |
|---|---|
| `-c`, `--config PFAD` | Pfad zur `config.yaml` / `.json`. |
| `-b`, `--backend auto\|kwin\|x11` | Backend erzwingen. |
| `-l`, `--lang de\|en` | Sprache der Ausgaben (Standard: `settings.language`, sonst `$LANG`). |
| `-v`, `--verbose` | Debug-Ausgaben. |
| `-V`, `--version` | Version ausgeben. |

## Ort der Konfiguration {#config-file-location}

fcwm sucht `$XDG_CONFIG_HOME/fcwm/config.yaml` (meist `~/.config/fcwm/config.yaml`), danach `config.yaml` im
Projektordner. `-c PFAD` wählt eine Datei ausdrücklich – auch eine `.json`-Datei mit gleicher Struktur.

## Neu laden und neu starten

Beides gibt es auch als Knöpfe auf der Seite **Einstellungen** der Web-UI.

```bash
fcwm reload     # laufende Instanz liest config.yaml neu ein (z. B. nach Handbearbeitung) – verschiebt nichts
fcwm restart    # startet die laufende Instanz neu
```
