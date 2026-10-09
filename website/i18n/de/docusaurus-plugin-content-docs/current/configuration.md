---
sidebar_position: 20
title: Konfigurationsreferenz
---

# Konfigurationsreferenz

Die Konfiguration liegt in `~/.config/fcwm/config.yaml` (siehe [Ort der Konfiguration](quick-start.md#config-file-location)).
`fcwm init` legt eine Startdatei aus deinen Monitoren an; das Paket enthält ausserdem eine vollständig
kommentierte `config.example.yaml` unter `/usr/share/doc/fcwm/`. Das meiste lässt sich in der
[Web-UI](web-ui.md) bearbeiten.

Schlüssel auf oberster Ebene:

| Schlüssel | Beschreibung |
|---|---|
| `settings` | Globale Einstellungen: Backend, Sprache, Adresse der Web-UI, Client-Erkennung, Abstand, Titelleisten, Trennlinien. |
| `monitors` | Monitor-Aliase mit ihrem Standardraster. |
| `default_profile` | Profil, das verwendet wird, wenn keines angegeben ist. |
| `profiles` | Benannte Layouts. |
| `hotkeys` | Globale Kurzbefehle (nächstes/vorheriges Layout, Stapel durchschalten). |

## settings {#settings}

```yaml
settings:
  backend: auto            # auto | kwin (Wayland + X11 unter Plasma) | x11 (wmctrl/xdotool)
  language: de             # de | en – Sprache der CLI-/Server-Meldungen
  web: {host: 127.0.0.1, port: 8765}
  match:
    caption_regex: '^EVE - (?P<char>.+)$'
    resource_class: '^steam_app_8500$'   # Steam/Proton-EVE; leer lassen für andere Launcher
  gap: 0                   # Abstand zwischen Rasterzellen in Pixel
  decoration: {top: 0, right: 0, bottom: 0, left: 0}   # nur x11-Backend
  min_size: [1024, 768]    # Warnung, wenn ein Feld kleiner ist (EVE-Minimum)
  titlebar: {hide: false}
  separator: {width: 2, color: "#3c3c3c", show: always}
```

| Schlüssel | Standard | Beschreibung |
|---|---|---|
| `backend` | `auto` | `kwin` funktioniert unter Plasma mit Wayland und X11; `x11` nutzt `wmctrl`/`xdotool` ohne KWin. |
| `language` | `$LANG` | Sprachcode für CLI- und Server-Meldungen (`en`, `de` oder eine [hinzugefügte Sprache](translations.md)). Die Web-UI hat eine eigene Auswahl (Einstellungen → Allgemein, im Browser gespeichert). Die CLI-Option `--lang` hat Vorrang. |
| `web.host` | `127.0.0.1` | Adresse, auf der die Web-UI lauscht. |
| `web.port` | `8765` | Port der Web-UI. |
| `match.caption_regex` | `^EVE - (?P<char>.+)$` | So werden EVE-Clients erkannt; die Gruppe `(?P<char>…)` liefert den Charakternamen. |
| `match.resource_class` | – | Optionaler Regex für die Fensterklasse (z. B. `^steam_app_8500$` für Steam/Proton). |
| `gap` | `0` | Abstand zwischen Rasterzellen in Pixel. |
| `decoration` | `0` | Grösse der Fensterdekoration. Nur für das `x11`-Backend, das die Client-Geometrie setzt; KWin setzt die Frame-Geometrie, dort wird nichts abgezogen. |
| `min_size` | `[1024, 768]` | Warnung, wenn ein Feld kleiner ist. |
| `titlebar` | `{hide: false}` | Titelleisten aller EVE-Clients ausblenden – siehe [Titelleisten](hotkeys-appearance.md#title-bars). |
| `separator` | `{width: 0}` | Trennlinie zwischen Clients: `width` (0–20 px), `color`, `show: always\|eve` – siehe [Trennlinien](hotkeys-appearance.md#separators). |

### Adresse der Web-UI {#web-ui-address}

```yaml
settings:
  web: {host: 127.0.0.1, port: 8765}
```

- `fcwm web --host H --port N` überschreibt beide Werte für einen Lauf.
- `fcwm open`, `fcwm reload` und `fcwm restart` verwenden den eingestellten Port, wenn `--port` fehlt.
- Die Werte lassen sich auch auf der Seite **Einstellungen** der Web-UI ändern. Eine Änderung wirkt nach einem
  **Neustart** (`fcwm restart` oder der Neustart-Knopf).

:::warning Nur lokal betreiben
Die Web-UI hat keine Anmeldung. Ihre API kann Fenster verschieben und die Konfiguration überschreiben.
Belasse es beim Standard `127.0.0.1` und mache den Port **nicht** im Netzwerk oder Internet erreichbar.
:::

## monitors {#monitors}

Monitore bekommen einen frei wählbaren Alias. Zuordnung über den Anschlussnamen (`fcwm monitors` zeigt sie)
oder über `index:` (0 = ganz links).

```yaml
monitors:
  left:
    output: DP-5
    grid: 2x2              # Spalten x Zeilen – Felder zeilenweise: 0 1 / 2 3
    reserve: auto          # Panel-Abzug: auto = KWin-Arbeitsbereich, oder {top, right, bottom, left}
  center:
    output: DP-1
    grid: 1x1
    reserve: auto
    padding: 0             # zusätzlicher Innenrand (Zahl oder {top: …, …})
  right:
    index: 2
    grid: 2x2
```

| Schlüssel | Beschreibung |
|---|---|
| `output` / `index` | Anschlussname (z. B. `DP-1`) oder Position von links. |
| `grid` | Standardraster: `"2x2"` oder `{cols, rows, col_weights, row_weights, row_col_weights}` – siehe [Raster und Gewichte](#grids-and-weights). |
| `reserve` | `auto` nimmt den KWin-Arbeitsbereich (ohne Panels); sonst `{top, right, bottom, left}` in Pixel. |
| `padding` | Zusätzlicher Innenrand: Zahl oder `{top, right, bottom, left}`. |
| `label` | Anzeigename in der Web-UI. Standard: das Monitormodell (EDID), bei gleichen Modellen mit Anschluss. |

## profiles {#profiles}

```yaml
default_profile: Solo-Mining

profiles:
  Solo-Mining:
    description: Main gross in der Mitte, Miner links und rechts
    hotkey: Meta+Ctrl+1
    assign:
      "Main": center:0
      "Alt 1": left:0
      "Alt 2": {monitor: left, slot: 1, span: [1, 2]}
    fill: [left, right]
    focus: Main
```

| Schlüssel | Beschreibung |
|---|---|
| `description` | Freitext. |
| `grids` | Monitor-Raster nur für dieses Profil überschreiben: `{left: 1x3, center: {cols: 2, rows: 2, col_weights: [2, 1]}}`. |
| `assign` | Charakter → Feld. Siehe [assign](#assign). |
| `fill` | Monitore, deren freie Felder weitere Clients erhalten. Siehe [fill](#fill-and-stacking). |
| `stack_overflow` | `true` (Standard): Sind alle Auffüll-Felder belegt, werden weitere Clients reihum darauf gestapelt. |
| `focus` | Charakter, der am Ende aktiviert wird. |
| `disabled_monitors` | Monitore, die dieses Profil nicht verwendet. |
| `subgrids` | Zellen in ein eigenes Raster teilen. Siehe [subgrids](#subgrids). |
| `overflow` | Überlauf-Felder. Siehe [overflow](#overflow). |
| `blocked` | Frei gehaltene Felder und Fensterzonen. Siehe [blocked](#blocked). |
| `stack_previews` | Vorschau-Leisten auf Stapeln. Siehe [Vorschauen](previews.md#preview-strip-on-a-stack). |
| `hotkey` | Globaler Kurzbefehl, der zu diesem Profil wechselt. |
| `stack_hotkeys` | Kurzbefehle pro Feld, die den Stapel dort durchschalten: `{"center:1": Meta+Ctrl+Q}`. |

### Feldnamen {#slot-names}

Felder werden als `monitor:feld` geschrieben, z. B. `center:0`. Sie sind **zeilenweise** nummeriert,
`0` = oben links (ein 2×2-Raster ist `0 1 / 2 3`). Zellen eines [Subgrids](#subgrids) heissen
`monitor:feld.sub`, z. B. `center:1.3`.

### assign {#assign}

```yaml
assign:
  "Main": center:0                                       # Kurzform
  "Alt 1": {monitor: left, slot: 0, span: [1, 2]}        # Langform: 1 Spalte x 2 Zeilen
  "Alt 2": center:1                                      # mehrere Charaktere auf einem Feld = Stapel
  "Alt 3": center:1                                      #   (erster Eintrag liegt oben)
  "Scout Alt": center:1.3                                # Subgrid-Zelle
```

Zugewiesene, aber nicht geöffnete Charaktere halten ihr Feld frei. Charaktere, die gerade nicht eingeloggt
sind, lassen sich in der Web-UI über „Charakter hinzufügen“ einplanen.

### fill und Stapeln {#fill-and-stacking}

Alle Clients ohne Zuweisung füllen alphabetisch die freien Felder der unter `fill` angegebenen Monitore.
Sind alle Auffüll-Felder belegt, werden weitere Clients reihum auf diesen Feldern **gestapelt**
(abschaltbar mit `stack_overflow: false`), sofern keine [Überlauf-Felder](#overflow) definiert sind.

### disabled_monitors {#disabled-monitors}

```yaml
disabled_monitors: [left, right]
```

Der Monitor bekommt keine Felder, wird beim Auffüllen übersprungen und in der Vorschau der Web-UI schraffiert.
Zuweisungen dorthin bleiben gespeichert und werden solange auf den übrigen Monitoren aufgefüllt.

### Raster und Gewichte {#grids-and-weights}

Ein Raster ist `"SPALTENxZEILEN"` oder eine Zuordnung:

```yaml
grids:
  center: {cols: 2, rows: 2, col_weights: [2, 1]}     # linke Spalte doppelt so breit
  right:
    cols: 2
    rows: 2
    row_weights: [1, 1]
    row_col_weights: {1: [75, 25]}                     # Zeile 1 hat eine eigene Spaltenteilung
```

- `col_weights` / `row_weights`: relative Grössen der Spalten / Zeilen.
- `row_col_weights`: Spaltengewichte pro Zeile – senkrechte Rasterlinien können pro Zeile verschieden sein.
- In der Web-UI werden sie durch Ziehen der Rasterlinien gesetzt (siehe [Web-UI](web-ui.md#grid-lines)).

### Subgrids {#subgrids}

Eine Zelle in ein eigenes Raster teilen, damit kleinere Clients hineinpassen:

```yaml
subgrids:
  "center:1": "2x2"
assign:
  "Scout Alt": "center:1.3"
```

Subzellen (`center:1.0`, `center:1.1` …) funktionieren wie normale Felder: zuweisen, stapeln, frei halten,
automatisch auffüllen. Ein Subgrid akzeptiert dieselbe Zuordnungsform (mit Gewichten) wie ein Raster.

### overflow {#overflow}

```yaml
overflow: [{cell: "right:2", max: 3}, "right:3"]
```

Überlauf-Felder werden nicht normal aufgefüllt. Sind alle Auffüll-Felder belegt, landen weitere Clients der
Reihe nach dort (als Stapel). `max` begrenzt die Zahl der Charaktere; das **letzte** Überlauf-Feld nimmt immer
alle übrigen auf und hat daher kein Maximum. Ohne Überlauf-Felder wird reihum gestapelt.

### blocked {#blocked}

Frei gehaltene Felder erhalten nie EVE-Clients, auch nicht beim Auffüllen oder Stapeln. Sie können leer
bleiben, ein anderes Programm oder einen Stapel von Programmen aufnehmen, neue Fenster auffangen oder
[Live-Vorschauen](previews.md) zeigen.

```yaml
blocked:
  "left:3": Browser                                  # nur frei halten (nur Beschriftung)
  "right:3": {label: RIFT, match: "RIFT"}            # erstes passendes Fenster hierher verschieben
  "right:2": {label: Code, match: "code", stack: true}
  "left:2": {label: Neue Fenster, catch_all: true, resize: false, exclude: "firefox|dolphin"}
  "center:1": {label: Alts, preview: hidden, show: eve}
```

| Schlüssel | Beschreibung |
|---|---|
| `label` | In der Web-UI angezeigter Name. |
| `match` | Regex (ohne Gross-/Kleinschreibung), geprüft gegen **Titel oder Fensterklasse** von Nicht-EVE-Fenstern. |
| `stack` | `true`: **alle** passenden Fenster landen als Stapel im Feld (erster Treffer oben). Standard: nur der erste Treffer. |
| `catch_all` | `true`: jedes neu geöffnete Fenster, das zu keinem anderen Feld passt, wird hierher verschoben (benötigt Auto-Platzierung). |
| `exclude` | Regex (Titel oder Klasse) für Fenster, die das Auffangfeld ignoriert. |
| `resize` | `false`: Fenster behält seine eigene Grösse (auf das Feld begrenzt, zentriert). Standard `true`. |
| `preview` | `all` oder `hidden` – macht das Feld zum [Vorschau-Feld](previews.md#preview-slots). |
| `show` | Für Vorschau-Felder: `always` (Standard) oder `eve` (nur solange ein EVE-Client aktiv ist). |

`match`, `stack`, `catch_all`, `exclude` und `resize` sind unter [Fensterzonen](window-zones.md) ausführlich
beschrieben.

### stack_previews {#stack-previews}

```yaml
stack_previews:
  "center:0": {mode: stack, edge: right, size: 20, show: always}
```

Siehe [Vorschauen](previews.md#preview-strip-on-a-stack).

## hotkeys {#hotkeys}

```yaml
hotkeys:
  next_profile: Meta+Ctrl+PgDown
  prev_profile: Meta+Ctrl+PgUp
  cycle_stack: Meta+Ctrl+Tab
```

Qt-Schreibweise (z. B. `Meta+Ctrl+Right`). Profil- und Stapel-Kurzbefehle werden pro Profil gesetzt
(`hotkey`, `stack_hotkeys`). Siehe [Kurzbefehle](hotkeys-appearance.md#hotkeys).

## Rasterberechnung {#grid-calculation}

1. **Monitorfläche:** logische Koordinaten (Rotation und Skalierung sind schon eingerechnet).
2. **Panel-Abzug** (`reserve`): `auto` nimmt den KWin-Arbeitsbereich (`MaximizeArea`, also ohne
   Taskleisten), alternativ manuell `{top, right, bottom, left}`.
3. **Padding** pro Monitor, danach das **Raster** `cols x rows` mit optionalen Gewichten und `gap`
   (der Abstand ist mindestens so breit wie die Trennlinie). Die Kanten werden kumuliert gerundet, damit keine
   Pixel verloren gehen.
4. **Dekoration:** KWin setzt die Frame-Geometrie (inkl. Titelleiste), dort wird nichts abgezogen.
   Das X11-Backend setzt die Client-Geometrie, dort wird `settings.decoration` abgezogen.

`span: [Spalten, Zeilen]` fasst Zellen zusammen.

## Speichern aus der Web-UI {#saving-from-the-web-ui}

Beim Speichern wird die Datei zuerst geprüft, die vorherige Version landet in `config.yaml.bak`. Mit
installiertem **ruamel.yaml** bleiben Kommentare und Formatierung ausserhalb des bearbeiteten Profils erhalten.
Ohne ruamel.yaml schreibt PyYAML die Datei neu, dabei gehen die Kommentare verloren.
