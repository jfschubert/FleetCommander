---
sidebar_position: 22
title: Aufbau & Entwicklung
---

# Aufbau & Entwicklung

## Modulstruktur {#module-structure}

```text
fcwm/
  geometry.py      Rect, Insets, GridSpec, Rasterberechnung (reine Mathematik, getestet)
  monitors.py      Monitorerkennung via kscreen-doctor (Fallback xrandr)
  config.py        YAML/JSON laden + validieren, Profile bearbeiten/zurückschreiben
  layout.py        EVE-Fenster filtern, Profil -> konkrete Platzierungen, Stapel
  backends/
    kwin.py        Wayland + X11: KWin-JS-Skript per D-Bus, Antwort über das Journal
    x11.py         wmctrl / xdotool (nur X11)
  app.py           gemeinsame Logik für CLI und Web (apply, preview, state)
  autoplace.py     Listener-Thread, Debounce/Batch-Platzierung, Kurzbefehle, Fixieren, Ereignisse (SSE)
  titlebar.py      Titelleisten über KWin-Fensterregeln
  separators.py    Trennlinien zwischen Clients (KWin-QML-Overlay)
  previews.py      Vorschau-Felder mit Live-Bildern (KWin-QML, WindowThumbnail)
  i18n.py          Meldungen nachschlagen (Texte in fcwm/locales/)
  locales/         Übersetzungen: web/<lang>.json, server/<lang>.json
  cli.py, web.py   Oberflächen
  maintenance.py   fcwm init / open / reload / restart / cleanup
  static/          Web-UI – ohne Build-Schritt, einfache Dateien, ausgeliefert von web.py:
    index.html       Markup + Icon-Sprite
    css/app.css      Styles
    js/*.js          klassische Skripte in Ladereihenfolge: i18n, core, model, cells, settings, move,
                     profiles, render, gridlines, controls (gemeinsamer globaler Gültigkeitsbereich)
packaging/         systemd-Dienst, Menüeintrag, Distributionspakete (arch/PKGBUILD …)
website/           diese Dokumentation (Docusaurus)
```

## Aus dem Quellordner starten {#running-from-a-checkout}

```bash
./fcwm.sh apply -n          # oder: python3 -m fcwm apply -n
```

`fcwm.sh` funktioniert auch als Ziel eines KDE-Kurzbefehls.

## Tests {#tests}

```bash
python3 -m unittest discover -s tests
```

## Dokumentation {#documentation}

Die Doku liegt in `website/` (Docusaurus 3, Englisch + Deutsch):

```bash
cd website
npm ci
npm start               # englischer Entwicklungsserver
npm run start:de        # deutscher Entwicklungsserver
npm run build           # statische Seite für beide Sprachen in website/build/
```

Die deutschen Übersetzungen liegen in `website/i18n/de/`. Veröffentlicht wird die Seite über
`.github/workflows/docs.yml` (GitHub Pages) bzw. `.gitlab-ci.yml` (GitLab Pages); `DOCS_URL` und
`DOCS_BASE_URL` überschreiben Adresse und Basispfad der Seite.

### Screenshots {#screenshots}

Die Screenshots in der Doku und auf der Startseite stammen aus `website/screenshots/take.py`. Das Skript
startet eine isolierte Web-UI mit der Demo-Konfiguration (nur Platzhalter-Charaktere) und rendert jede Seite
offscreen auf Englisch und Deutsch (benötigt PyQt6-WebEngine):

```bash
python3 website/screenshots/take.py
```

## Releases {#releases}

`packaging/bump-version.sh X.Y.Z "Changelog-Zeile"` setzt die Version überall, wo sie steht. Ein Push des
Tags `vX.Y.Z` startet `.github/workflows/release.yml`: Tests, Versionsprüfung, die Pakete für Arch, Debian und
Fedora sowie Wheel und Sdist und ein GitHub-Release mit allen Dateien und `SHA256SUMS`. Details:
[`packaging/README.md`](https://github.com/jfschubert/FleetCommander/blob/master/packaging/README.md#releasing-a-new-version).
