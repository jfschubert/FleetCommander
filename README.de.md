# FleetCommander (fcwm)

🇬🇧 [English version](README.md)

Ordnet EVE-Online-Clients unter KDE Plasma (Wayland **und** X11) anhand eines Rasters pro Monitor an.
Profile legen fest, welcher Charakter in welchem Slot landet. Steuerung per CLI, KDE-Kurzbefehl oder Web-UI.

## Abhängigkeiten

| Was | Wofür | Arch | Debian/Ubuntu |
|---|---|---|---|
| Python ≥ 3.10 | Laufzeit | `python` | `python3` |
| PyYAML | YAML-Konfiguration (für JSON nicht nötig) | `python-yaml` | `python3-yaml` |
| `kscreen-doctor` | Monitore erkennen (Fallback, wenn KWin nicht antwortet) | `kscreen` | `kscreen` |
| `busctl`, `journalctl` | D-Bus-Aufrufe an KWin und Rückgabewerte lesen (systemd, normalerweise vorhanden) | `systemd` | `systemd` |
| *optional* ruamel.yaml | Kommentare in der config.yaml beim Speichern aus der Web-UI erhalten | `python-ruamel-yaml` | `python3-ruamel.yaml` |
| *optional* `wmctrl` / `xdotool` / `xrandr` | X11-Backend ohne KWin | `wmctrl xdotool xorg-xrandr` | `wmctrl xdotool x11-xserver-utils` |

Unter Plasma brauchst du nur Python und PyYAML. Die Web-UI nutzt nur die Standardbibliothek.

## Installation (Arch Linux)

fcwm wird als ein Arch-Paket verteilt (PKGBUILD in `packaging/arch/`):

```bash
git clone https://github.com/jfschubert/FleetCommander.git
cd FleetCommander/packaging/arch
makepkg -si                                   # baut, führt die Tests aus, installiert
fcwm init                                    # Startkonfiguration aus deinen Monitoren -> ~/.config/fcwm/config.yaml
systemctl --user enable --now fcwm           # läuft mit der Plasma-Sitzung
```

Die Web-UI ist unter http://127.0.0.1:8765/ erreichbar oder über „FleetCommander“ im Anwendungsmenü
(`fcwm open`).

Das Paket installiert `/usr/bin/fcwm`, den systemd-Benutzerdienst `fcwm.service`, den Menüeintrag und die
Dokumentation (`/usr/share/doc/fcwm/`, inkl. `config.example.yaml` mit allen Funktionen). **Vor dem
Deinstallieren** als normaler Benutzer:

```bash
systemctl --user disable --now fcwm
fcwm cleanup        # entfernt fcwms KWin-Fensterregeln, Farbschemata und globale Kurzbefehle
sudo pacman -R fcwm
```

Die Konfiguration in `~/.config/fcwm/` bleibt erhalten.

**Umstieg von `evewm`** (der frühere Name): Das Paket ersetzt es. Beim ersten Start wird `~/.config/evewm`
nach `~/.config/fcwm` kopiert (der alte Ordner bleibt als Sicherung) und alte `evewm-*`-Fensterregeln und
Kurzbefehle werden aufgeräumt. Dienst umstellen: `systemctl --user disable --now evewm; systemctl --user enable --now fcwm`.

**Neu laden / neu starten** (auch als Knöpfe in der Web-UI, Fenster „Konfiguration“):

```bash
fcwm reload     # laufende Instanz liest config.yaml neu ein (z. B. nach Handbearbeitung) – verschiebt nichts
fcwm restart    # startet die laufende Instanz neu (systemd-Dienst oder von Hand gestartetes `fcwm web`)
```

**Aktualisieren:** `git pull && cd packaging/arch && makepkg -sif`, danach `fcwm restart`. Getestet mit Plasma 6.7 / KWin 6.7 (Wayland). fcwm
ordnet Fenster nur an, schaltet und zeigt Vorschauen – es sendet nie Eingaben an Clients (gleiche Kategorie wie
EVE-O Preview).

## Schnellstart

```bash
fcwm monitors                 # Anschlussnamen + Arbeitsbereich (ohne Panels)
fcwm windows             # erkannte EVE-Clients
fcwm apply -n            # Testlauf mit dem Standardprofil
fcwm apply Fleet-Fight   # Profil anwenden
fcwm watch Solo-Mining   # Listener: neue Clients beim Einloggen automatisch platzieren
fcwm watch --initial     # … und beim Start bereits offene Clients einmal platzieren
fcwm web                 # Web-UI auf http://127.0.0.1:8765/ (inkl. Listener)
fcwm --lang en apply -n  # Sprache der Ausgaben (de/en)
```

**Hotkeys:** Systemeinstellungen → Tastatur → Kurzbefehle → *Neu hinzufügen* → *Befehl*:
`fcwm apply Fleet-Fight`.

**Autostart:** `systemctl --user enable --now fcwm` (siehe Installation).

## Listener & Auto-Platzierung

- Unter KWin ereignisgesteuert: ein dauerhaft geladenes KWin-Skript (`fcwm_listener`) meldet
  `windowAdded` / `captionChanged` / `windowRemoved`; Python folgt dem Journal (`journalctl -f`).
  Ohne KWin (X11) wird alle 2 s die Fensterliste verglichen.
- Ein Client gilt als eingeloggt, sobald sein Titel vom Startfenster „EVE“ zu „EVE - Name“ wechselt.
- **Mehrere Logins gleichzeitig** werden gesammelt (1 s Ruhe, höchstens 4 s) und in einem Rutsch
  platziert. Bereits platzierte Clients werden nicht bewegt und behalten ihren Slot – ein später
  einloggender Alt rutscht in den nächsten *freien* Platz, statt andere zu verdrängen.
- In der Web-UI: Checkbox „Auto-Platzierung“ (Kopfzeile bzw. Seitenleiste) und Profilwahl. Der
  Zustand liegt in `fcwm-state.json` neben der Konfiguration und übersteht Neustarts.
  Auch bei ausgeschalteter Auto-Platzierung erscheinen Logins als Benachrichtigung und im Ereignis-Log.
- Beim Beenden (Strg+C/SIGTERM) wird das KWin-Skript wieder entladen.

## Kurzbefehle, Fixieren, Titelleisten

Alles in der Web-UI einstellbar; benötigt KWin (Plasma) und läuft, solange `fcwm web` oder `fcwm watch` aktiv ist.

- **Kurzbefehle** (Fenster „Kurzbefehle“): nächstes / vorheriges Layout, aktiven Stapel durchschalten. Pro Profil
  ein eigener Kurzbefehl (Feld „Kurzbefehl“ neben dem Namen) und pro Feld ein Stapel-Kurzbefehl (⌨ auf dem Feld).
  Feld anklicken, Kombination drücken; Entf löscht, Esc bricht ab. Es sind echte globale KDE-Kurzbefehle
  (in den Systemeinstellungen unter KWin sichtbar). Ein Layout-Wechsel macht das Layout gleichzeitig zum
  **aktiven Layout** (▸ im Tab) – das nutzen Auto-Platzierung und Stapel-Kurzbefehle.
- **Stapel durchschalten:** holt den untersten Client des Stapels nach vorn und aktiviert ihn – mehrfach
  drücken geht reihum durch alle. „Aktiver Stapel“ ist der Stapel des gerade aktiven EVE-Fensters.
- **Fixieren** (Kopfzeile): EVE-Clients springen nach Verschieben, Grössenänderung, Maximieren oder Kacheln
  sofort an ihren Platz zurück. Beim Einschalten werden sie dort fixiert, wo sie gerade sind; jedes Anwenden
  (Knopf, Kurzbefehl, Auto-Platzierung) aktualisiert die Plätze.
- **Titelleisten:** für alle EVE-Clients ausblenden und/oder einfärben, zusätzlich eine Farbe pro Charakter.
  Umgesetzt über eigene KWin-Fensterregeln (`fcwm-…` in `~/.config/kwinrulesrc`, andere Regeln bleiben
  unberührt) und kleine Farbschemata unter `~/.local/share/color-schemes/FCWM-*.colors`. Wirkt auch, wenn
  das Tool nicht läuft. **Beim Aus-/Einblenden werden die Clients neu ausgerichtet** – ohne Titelleiste
  schrumpft sonst der Rahmen und oben bleibt eine Lücke.
- **Trennlinie zwischen Clients** (Fenster „Titelleisten“): Breite in Pixel und Farbe. Das Raster lässt dafür
  eine Lücke dieser Breite; gezeichnet wird nur dort, wo zwei Fenster aneinanderstossen – eine Linie pro
  Kante, nicht am Rand und nicht neben leeren Feldern. Die Linien sind klickdurchlässige KWin-Overlays,
  die sich wie Hintergrund verhalten: Eine Linie verschwindet, sobald ein Fenster, das *über* ihren beiden
  Nachbarn liegt, die Lücke überdeckt (z. B. der fokussierte Browser), und wenn auf einer Seite kein
  sichtbarer Client steht. Optional nur solange ein EVE-Client (oder ein Fenster aus einem frei gehaltenen Feld)
  aktiv ist.

```yaml
hotkeys:
  next_profile: Meta+Ctrl+PgDown
  prev_profile: Meta+Ctrl+PgUp
  cycle_stack: Meta+Ctrl+Tab
settings:
  titlebar: {hide: false, color: "#2a6f97"}
  separator: {width: 2, color: "#3c3c3c"}
characters:
  "Alt 1": {color: "#b42828"}
profiles:
  Fleet-Fight:
    hotkey: Meta+Ctrl+2
    stack_hotkeys: {"center:1": Meta+Ctrl+Q}
```

## Sprache

Web-UI: Auswahl Deutsch/English oben rechts (wird im Browser gespeichert). CLI: `--lang`, sonst
`settings.language` in der Konfiguration, sonst `$LANG`.

## Web-UI / Profil-Editor

`fcwm web` → http://127.0.0.1:8765/

- **Drag & Drop:** Charaktere aus der Palette in ein Feld ziehen. Auf ein belegtes Feld ziehen **stapelt**
  (der neue liegt oben), mit **Shift** werden die beiden stattdessen getauscht. Zurück auf die Palette
  ziehen entfernt die Zuweisung.
- **Stapel:** Mehrere Charaktere teilen sich exakt denselben Platz. Im Feld steht die Liste, oben = sichtbar;
  ▲ holt einen Eintrag nach oben, einzelne Einträge lassen sich wieder herausziehen. Beim Anwenden
  holt das Tool die Fenster so nach vorn, dass der oberste Eintrag oben liegt. ⇥/⤓ gelten für den ganzen Stapel.
- **Überzählige werden immer gestapelt:** Sind alle Auffüll-Felder belegt, landen weitere Clients reihum
  als Stapel auf diesen Feldern (abschaltbar mit `stack_overflow: false` im Profil). Ein Drop auf ein
  automatisch belegtes Feld pinnt den dortigen Client fest und stapelt darauf.
- **Rasterlinien verschieben:** Die Linien zwischen Spalten/Zeilen in der Vorschau mit der Maus ziehen
  (◆-Griff). Ein Hinweis zeigt Prozent und Pixel beider Seiten, **Shift** rastet auf 1/12 ein, jede Seite
  bleibt mindestens 5 % breit. **Senkrechte Linien gelten pro Zeile:** Ein Segment ziehen ändert nur diese
  Zeile (z. B. Zeile 1 = 50:50, Zeile 2 = 75:25), mit **Strg** wird die Linie über alle Zeilen verschoben.
  Gespeichert wird als `col_weights`/`row_weights` bzw. `row_col_weights: {1: [75, 25]}`; „Linien gleichmässig“
  auf der Monitor-Karte setzt zurück. Ändert sich die Spalten- bzw. Zeilenzahl, werden die Linien dieser
  Achse wieder gleichmässig.
- **Subgrids (kleinere Clients):** ⊞ auf einem leeren Feld teilt es in ein eigenes Raster (Standard 2×2).
  Die Subzellen heissen `center:1.0`, `center:1.1` … und funktionieren wie normale Felder: zuweisen,
  stapeln, frei halten, automatisch auffüllen. Über das Schild „⊞ 2×2“ lassen sich Spalten/Zeilen ändern oder
  die Teilung aufheben (Charaktere landen dann als Stapel in der ganzen Zelle). Auch die Linien im Subgrid
  lassen sich ziehen. In der Konfiguration:
  ```yaml
  subgrids:
    "center:1": "2x2"
  assign:
    "Scout Alt": "center:1.3"
  ```
- **Überlauf-Felder:** ⇊ auf einem leeren Feld. Überlauf-Felder werden nicht normal aufgefüllt; sind alle
  Auffüll-Felder belegt, landen weitere Clients der Reihe nach dort (als Stapel). Über das Schild „⇊ 1 · max 3“
  lassen sich Reihenfolge und **max. Charaktere** einstellen – das letzte Überlauf-Feld nimmt immer alle
  übrigen auf und hat daher kein Maximum. Ohne Überlauf-Felder wird wie bisher reihum gestapelt.
  ```yaml
  overflow: [{cell: "right:2", max: 3}, "right:3"]
  ```
- **Felder frei halten** (z. B. für Browser oder RIFT): ⊘ auf einem leeren Feld. Das Feld wird nie mit
  EVE-Clients belegt, auch nicht beim Auffüllen oder Stapeln. Optional ein Fenster zuordnen (Titel oder
  Fensterklasse aus der Liste oder ein Regex-Muster wie `RIFT|Brave`): Es wird beim Anwenden des Profils
  mit in das Feld verschoben. ✎ bzw. Doppelklick bearbeitet, ✕ gibt das Feld wieder frei. In der Konfiguration:
  ```yaml
  blocked:
    "right:3": {label: RIFT, match: "RIFT"}
    "left:3": Browser          # nur frei halten
  ```
- **Vorschau-Felder (wie EVE-O Preview):** In einem frei gehaltenen Feld (⊘ → ✎) „Vorschau“ wählen:
  *alle Clients* oder *nur verdeckte* (hinten im Stapel bzw. minimiert). Das Feld zeigt Live-Bilder der
  Clients als Kacheln mit Charakternamen (in der Titelleisten-Farbe), der aktive ist hervorgehoben, ein Klick
  wechselt zum Client. Gerendert von KWin selbst (`WindowThumbnail`), ohne Bildschirmaufnahme.
  **Sichtbar:** *immer* (Standard, wie EVE-O Preview – liegt dann auch über anderen Programmen) oder *nur
  solange ein EVE-Client aktiv ist*. Nur solange `fcwm web`/`watch` läuft.
- **Vorschau-Leiste auf einem Stapel:** ▣ auf einem Feld. Eine Leiste mit Live-Bildern an einer Kante des
  Stapels (unten/oben/links/rechts, Grösse in %), Inhalt: *die anderen (verdeckten) Clients dieses Stapels*
  oder *alle Clients*. „Verdeckte“ verschwindet von selbst, wenn nichts verdeckt ist.
  ```yaml
  blocked:
    "right:3": {label: Alts, preview: hidden, show: eve}   # preview: all|hidden, show: always|eve
  stack_previews:
    "center:0": {mode: stack, edge: right, size: 20}        # mode: stack|all
  ```
- **Feld-Typen verschieben:** Frei gehaltene Felder (auch Vorschau/Browser/RIFT) direkt ziehen, Überlauf-
  und Kurzbefehl-Schilder ziehen, ein Subgrid am Schild „⊞“ ziehen (zieht samt Inhalt um). Auf einem belegten
  Ziel wird getauscht.
- **Monitore nicht verwenden:** Checkbox „Monitor verwenden“ auf der Monitor-Karte bzw.
  `disabled_monitors: [left, right]` im Profil. Der Monitor bekommt keine Felder, wird beim Auffüllen
  übersprungen und in der Vorschau schraffiert. Zuweisungen dorthin bleiben gespeichert und werden
  solange auf den übrigen Monitoren aufgefüllt.
- **Feld-Werkzeuge** (beim Überfahren): ⇥ / ⤓ über mehrere Spalten/Zeilen ausdehnen (weiterklicken setzt
  zurück), Pin-Symbol: automatisch platzierten Client an seinem Platz festpinnen, ✕ entfernen.
- **Raster pro Monitor** über die Karten unter der Vorschau (Spalten/Zeilen ±, „freie Felder auffüllen“).
  Beim Ändern behalten Zuweisungen ihre Spalte/Zeile, solange diese im neuen Raster noch existiert.
- **Profile:** ＋ (neu), Duplizieren, Umbenennen (Namensfeld), Als Standard (★), Löschen.
  Ungespeicherte Profile sind mit ◆ markiert. *Anwenden* nutzt auch ungespeicherte Änderungen.
- Charaktere, die gerade nicht eingeloggt sind, lassen sich über „Charakter hinzufügen“ einplanen.
- Fenster lassen sich über `—` oder Doppelklick auf die Titelleiste einklappen.

Beim Speichern wird die Datei zuerst geprüft, die vorherige Version landet in `config.yaml.bak`.
Mit installiertem **ruamel.yaml** bleiben Kommentare und Formatierung ausserhalb des bearbeiteten
Profils erhalten. Ohne ruamel.yaml schreibt PyYAML die Datei neu, dabei gehen die Kommentare verloren.

## Aufbau

```
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
  i18n.py          Meldungen DE/EN
  cli.py, web.py   Oberflächen
  maintenance.py   fcwm init / open / cleanup
packaging/         systemd-Dienst, Menüeintrag, arch/PKGBUILD
  static/index.html
```

## Rasterberechnung

1. **Monitorfläche:** logische Koordinaten (Rotation und Skalierung sind schon eingerechnet).
2. **Panel-Abzug** (`reserve`): `auto` nimmt den KWin-Arbeitsbereich (`MaximizeArea`, also ohne
   Taskleisten), alternativ manuell `{top, right, bottom, left}`.
3. **Padding** pro Monitor, danach **Raster** `cols x rows` mit optionalen `col_weights`/`row_weights`
   und `gap`. Die Kanten werden kumuliert gerundet, damit keine Pixel verloren gehen.
4. **Dekoration:** KWin setzt die Frame-Geometrie (inkl. Titelleiste), dort wird nichts abgezogen.
   Das X11-Backend setzt die Client-Geometrie, dort wird `settings.decoration` abgezogen.

Slots werden zeilenweise nummeriert (`0` = oben links). `span: [Spalten, Zeilen]` fasst Zellen zusammen.
Zugewiesene, aber nicht geöffnete Charaktere halten ihren Slot frei. Alle übrigen Clients füllen
alphabetisch die freien Slots der unter `fill` angegebenen Monitore, danach wird reihum gestapelt.

## Hinweise / Grenzen

- Das KWin-Backend schreibt pro Abfrage bzw. Fenster-Ereignis ein paar Zeilen ins User-Journal (Rückkanal des Skripts).
- Die Web-UI lauscht nur auf `127.0.0.1`. Sie kann Fenster verschieben und die Konfiguration überschreiben.
- Tests: `python3 -m unittest discover -s tests`

## Lizenz

GPL-3.0 – siehe [LICENSE](LICENSE).
