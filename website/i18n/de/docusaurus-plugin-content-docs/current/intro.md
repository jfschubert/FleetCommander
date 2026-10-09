---
slug: /
sidebar_position: 1
title: Einführung
description: FleetCommander (fcwm) ordnet EVE-Online-Clients unter KDE Plasma in einem Raster pro Monitor an.
---

# FleetCommander

**FleetCommander** (`fcwm`) ordnet EVE-Online-Clients unter KDE Plasma (Wayland **und** X11) anhand eines
Rasters pro Monitor an. Profile legen fest, welcher Charakter in welchem Feld landet. Gesteuert wird per CLI,
KDE-Kurzbefehl oder über die eingebaute Web-UI.

## Funktionen

- **Raster pro Monitor** mit verschiebbaren Rasterlinien, Spalten-/Zeilen-Spans und verschachtelten
  **Subgrids** für kleinere Clients.
- **Profile**: Charaktere Feldern zuweisen, freie Felder automatisch auffüllen, Layouts per Kurzbefehl wechseln.
- **Stapel**: mehrere Clients teilen sich einen Platz; ein Kurzbefehl schaltet reihum durch.
- **Auto-Platzierung**: ein Listener platziert Clients, sobald sie sich einloggen – gleichzeitige Logins werden gesammelt.
- **Fensterzonen**: Felder für andere Programme frei halten (Browser, RIFT, Editor …), passende Fenster dort
  stapeln oder jedes neu geöffnete Fenster in einem Feld auffangen.
- **Live-Vorschauen** wie EVE-O Preview, gerendert von KWin selbst (ohne Bildschirmaufnahme).
- **Fixieren**, farbige oder ausgeblendete **Titelleisten** pro Charakter und **Trennlinien** zwischen Clients.
- **Web-UI** mit Drag-&-Drop-Profil-Editor, auf Deutsch und Englisch.

fcwm ordnet Fenster nur an, schaltet und zeigt Vorschauen – es **sendet nie Eingaben an Clients** (gleiche
Kategorie wie EVE-O Preview). Getestet mit Plasma 6.7 / KWin 6.7 (Wayland).

## Wie geht es weiter?

- [Installation](installation.md) – Abhängigkeiten und das Arch-Paket.
- [Schnellstart & CLI](quick-start.md) – die ersten Befehle und alle Befehle im Überblick.
- [Web-UI](web-ui.md) – der Profil-Editor.
- [Konfigurationsreferenz](configuration.md) – alle Schlüssel der `config.yaml`.
