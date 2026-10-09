<img src="fcwm/static/fcwm.svg" alt="FleetCommander" width="96" align="right">

# FleetCommander (fcwm)

🇬🇧 [English version](README.md) · 📖 **[Dokumentation](https://jfschubert.github.io/FleetCommander/de/)**

Ordnet EVE-Online-Clients unter KDE Plasma (Wayland **und** X11) anhand eines Rasters pro Monitor an.
Profile legen fest, welcher Charakter in welchem Slot landet. Steuerung per CLI, KDE-Kurzbefehl oder Web-UI.

fcwm ordnet Fenster nur an, schaltet und zeigt Vorschauen – es sendet nie Eingaben an Clients (gleiche
Kategorie wie EVE-O Preview). Getestet mit Plasma 6.7 / KWin 6.7 (Wayland).

## Funktionen

- **Raster pro Monitor** mit ziehbaren Rasterlinien, Spans und verschachtelten **Subgrids** für kleinere Clients
- **Profile** mit Charakter-Zuweisungen, automatischem Auffüllen, **Stapeln** und **Überlauf**-Feldern
- **Auto-Platzierung**: Clients werden beim Einloggen platziert (gleichzeitige Logins werden gesammelt)
- **Fensterzonen**: Felder für Browser, RIFT, Editor … frei halten – passende Fenster dort stapeln oder
  jedes neu geöffnete Fenster in einem Feld auffangen
- **Globale Kurzbefehle** zum Layout-Wechsel und Stapel-Durchschalten, Fenster **fixieren**
- **Live-Vorschauen** wie EVE-O Preview, gerendert von KWin (ohne Bildschirmaufnahme)
- Farbige / ausgeblendete **Titelleisten** pro Charakter und **Trennlinien** zwischen Clients
- **Web-UI** mit Drag-&-Drop-Profil-Editor (Deutsch / Englisch)

## Installation (Arch Linux)

```bash
git clone https://github.com/jfschubert/FleetCommander.git
cd FleetCommander/packaging/arch
makepkg -si                          # baut, führt die Tests aus, installiert
fcwm init                            # Startkonfiguration -> ~/.config/fcwm/config.yaml
systemctl --user enable --now fcwm   # läuft mit der Plasma-Sitzung
```

Pakete für andere Distributionen: siehe [`packaging/README.md`](packaging/README.md).
Abhängigkeiten, Aktualisieren und Deinstallieren: [Installation](https://jfschubert.github.io/FleetCommander/de/installation/).

## Schnellstart

```bash
fcwm monitors            # Anschlussnamen + Arbeitsbereich
fcwm windows             # erkannte EVE-Clients
fcwm apply -n            # Testlauf mit dem Standardprofil
fcwm apply Fleet-Fight   # Profil anwenden
fcwm watch --initial     # Clients beim Einloggen automatisch platzieren
fcwm web                 # Web-UI auf http://127.0.0.1:8765/ (inkl. Listener)
```

Die vollständige CLI- und Konfigurationsreferenz, die Anleitung zur Web-UI und mehr stehen in der
**[Dokumentation](https://jfschubert.github.io/FleetCommander/de/)** (Quellen in [`website/`](website/)).

Tests: `python3 -m unittest discover -s tests`

fcwm in deine Sprache übersetzen? Siehe [Übersetzungen](https://jfschubert.github.io/FleetCommander/de/translations/).

## Lizenz

GPL-3.0 – siehe [LICENSE](LICENSE). Das App-Icon ist eine eigene Gestaltung dieses Projekts; die UI-Symbole stammen von [Lucide](https://lucide.dev) (ISC).

EVE Online® und Fenris Creations™ sowie alle zugehörigen Logos und Elemente sind Marken von Fenris Creations
(ehemals CCP Games). FleetCommander ist ein inoffizielles Drittanbieter-Tool und steht in keiner Verbindung zu
Fenris Creations. Details: [NOTICE](NOTICE).
