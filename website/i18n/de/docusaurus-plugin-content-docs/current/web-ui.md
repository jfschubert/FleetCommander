---
sidebar_position: 10
title: Web-UI
---

# Web-UI

Start mit `fcwm web` (oder über den systemd-Dienst), dann <http://127.0.0.1:8765/> öffnen – oder
`fcwm open`, oder das [Programmfenster](#app-window) über „FleetCommander“ im Anwendungsmenü. Adresse und Port sind
[einstellbar](configuration.md#web-ui-address). Die Web-UI enthält den [Listener](auto-placement.md).

Die Sprache (Deutsch/English) wird unter **Einstellungen → Allgemein** gewählt und im Browser gespeichert.

## Programmfenster {#app-window}

Lieber ohne Browser-Tab? `fcwm app` – oder einfach „FleetCommander“ im Anwendungsmenü – öffnet dieselbe Web-UI
in einem eigenen Fenster und startet fcwm vorher, falls es noch nicht läuft. Einzustellen gibt es nichts: Es ist
genau die Seite aus dem Browser (F5 / Strg+R lädt neu). Links zu anderen Seiten öffnen sich im Standardbrowser;
„Im Browser öffnen“ im Rechtsklick-Menü des Menüeintrags (oder `fcwm open`) liefert weiterhin den Browser-Tab.
Ein [Auffang-Feld](window-zones.md) fängt dieses Fenster nie ein.

Das Fenster braucht **PyQt6-WebEngine** (Arch `python-pyqt6-webengine`, Debian/Ubuntu `python3-pyqt6.qtwebengine`,
Fedora `python3-pyqt6-webengine`, openSUSE `python3-PyQt6-WebEngine`). Fehlt es, sagt `fcwm app` das und öffnet
stattdessen den Browser.

Das Fenster hat FleetCommanders **eigene Titelleiste** statt der von KDE: Kopfzeile ziehen zum Verschieben,
Doppelklick zum Maximieren, **– □ ✕** rechts, an den Fensterkanten ziehen zum Ändern der Grösse. Verschieben und
Grössenänderung übernimmt weiterhin KWin, Einrasten an Bildschirmkanten funktioniert also. `fcwm app --native-frame`
behält die KDE-Titelleiste.

## Seiten {#pages}

Die Oberfläche hat drei Seiten:

- **Layout** (Hauptseite): Profile, die Monitor-Vorschau mit allen Feldern, die Charakter-Palette, die
  Monitor-Karten, Anwenden, Auto-Platzierung und Fixieren.
- **Einstellungen**: Sprache, globale Kurzbefehle, Titelleisten / Trennlinien / Charakterfarben, Debug-Infos
  (Backend, Versionen, Clients, Monitore – mit Kopieren-Knopf für Fehlerberichte), die Konfigurationsdatei mit
  Knöpfen zum **Neu laden** und **Neu starten** sowie Adresse/Port der Web-UI (wirkt nach einem Neustart).
- **Über**: Version, Links (Dokumentation, GitHub, Fehler melden, Lizenz), Mitwirkende, rechtlicher Hinweis – und
  wie man mit einer **ISK-Spende** im Spiel an *Mister Forever* Danke sagen kann. Das Charakterporträt wird erst
  beim Öffnen der Seite vom offiziellen EVE-Bildserver geladen.

Längere Hilfetexte stecken hinter kleinen **i**-Symbolen – mit der Maus darüberfahren, um sie zu lesen.

## Profile {#profiles}

＋ legt ein neues Profil an; umbenannt wird im Namensfeld. Das Profil-Menü **⋯** enthält **Duplizieren**,
**Als Standard** (★) und **Löschen**. Beschreibung, Fokus-Charakter und Profil-Kurzbefehl liegen unter
**Weitere Profil-Optionen**. Ungespeicherte Profile sind mit ◆ markiert; *Anwenden* nutzt auch ungespeicherte
Änderungen.

## Charaktere zuweisen {#assigning-characters}

- **Drag & Drop:** Charaktere aus der Palette in ein Feld ziehen. Auf ein belegtes Feld ziehen **stapelt**
  (der neue liegt oben), mit **Shift** werden die beiden stattdessen getauscht. Zurück auf die Palette ziehen
  entfernt die Zuweisung.
- **Stapel:** Mehrere Charaktere teilen sich exakt denselben Platz. Im Feld steht die Liste, oben = sichtbar.
  Jede Stapelzeile hat eigene Knöpfe: ▲ holt den Eintrag nach oben, das Pin-Symbol pinnt ihn fest, ✕ entfernt
  ihn. Einzelne Einträge lassen sich auch wieder herausziehen. Beim Anwenden holt fcwm die Fenster so nach vorn,
  dass der oberste Eintrag oben liegt.
- **Überzählige werden immer gestapelt:** Sind alle Auffüll-Felder belegt, landen weitere Clients reihum als
  Stapel auf diesen Feldern (abschaltbar mit `stack_overflow: false`). Ein Drop auf ein automatisch belegtes
  Feld pinnt den dortigen Client fest und stapelt darauf.
- Charaktere, die gerade nicht eingeloggt sind, lassen sich über **Charakter hinzufügen** einplanen.

## Das Feld-Menü (⚙) {#the-slot-menu}

Jedes Feld hat einen Zahnrad-Knopf **⚙**, der sein Aktionsmenü öffnet. Welche Einträge erscheinen, hängt vom
Feld ab.

**Client-Felder:**

| Menüeintrag | Wirkung |
|---|---|
| breiter (über Spalten) / höher (über Zeilen) | Über mehrere Spalten / Zeilen ausdehnen (weiterklicken über den Rand setzt zurück). Gilt für den ganzen Stapel. |
| An dieser Stelle festpinnen | Einen automatisch platzierten Client an seinem Platz festpinnen. |
| Kurzbefehl für dieses Feld (Stapel durchschalten) | Kurzbefehl, der den Stapel in diesem Feld durchschaltet. |
| Vorschau-Leiste auf diesem Stapel | Leiste mit Live-Bildern an einer Kante des Stapels – siehe [Vorschauen](previews.md#preview-strip-on-a-stack). |
| Zelle in ein Subgrid teilen | Ein leeres Feld in ein eigenes Raster teilen (Standard 2×2) – siehe [Subgrids](#subgrids). |
| Als Überlauf-Feld verwenden | Das Feld zum [Überlauf-Feld](configuration.md#overflow) machen. |
| Frei halten / für andere Fenster (Browser, RIFT, Auffang …) | Das Feld zu einem frei gehaltenen Feld / einer [Fensterzone](window-zones.md) machen. |
| Zuweisung entfernen | Die Charakter-Zuweisung entfernen. |

**Frei gehaltene Felder:**

| Menüeintrag | Wirkung |
|---|---|
| Bearbeiten (Name, Fenster, Vorschau) | Den Feld-Editor öffnen (Doppelklick geht auch). |
| Kurzbefehl … | Kurzbefehl, der den [Fensterstapel](window-zones.md#window-stacks) in diesem Feld durchschaltet. |
| Wieder für Clients freigeben | Wieder zu einem normalen Feld machen. |

### Der Feld-Editor {#the-slot-editor}

Für frei gehaltene Felder hat der Editor einen Namen, das Fenstermuster (Titel/Klasse eines offenen Fensters
wählen oder einen Regex eingeben) und diese Optionen – siehe [Fensterzonen](window-zones.md):

| Option | Konfigurationsschlüssel |
|---|---|
| Alle passenden Fenster stapeln | `stack: true` |
| Auffang-Feld für neue Fenster, mit dem Feld „Nicht einfangen (Titel/Klasse, Regex)“ | `catch_all: true`, `exclude` |
| Fenstergrösse beibehalten | `resize: false` |
| Vorschau | `preview`, `show` – siehe [Vorschauen](previews.md#preview-slots) |

## Rasterlinien {#grid-lines}

Die Linien zwischen Spalten/Zeilen in der Vorschau mit der Maus ziehen (◆-Griff). Ein Hinweis zeigt Prozent und
Pixel beider Seiten, **Shift** rastet auf 1/12 ein, jede Seite bleibt mindestens 5 % breit.

**Senkrechte Linien gelten pro Zeile:** Ein Segment ziehen ändert nur diese Zeile (z. B. Zeile 1 = 50:50,
Zeile 2 = 75:25), mit **Strg** wird die Linie über alle Zeilen verschoben. Gespeichert wird als
`col_weights`/`row_weights` bzw. `row_col_weights: {1: [75, 25]}`. „Linien gleichmässig“ auf der Monitor-Karte
setzt zurück. Ändert sich die Spalten- bzw. Zeilenzahl, werden die Linien dieser Achse wieder gleichmässig.

## Monitor-Karten {#monitor-cards}

Unter der Vorschau gibt es eine Karte pro Monitor: Spalten/Zeilen ±, „freie Felder auffüllen“, „Linien
gleichmässig“ und **Monitor verwenden** (abgewählt = `disabled_monitors`). Beim Ändern des Rasters behalten
Zuweisungen ihre Spalte/Zeile, solange diese im neuen Raster noch existiert.

Jede Karte zeigt den **Namen** des Monitors: standardmässig sein Modell aus den Monitordaten (EDID, z. B.
„DELL G3223Q“; bei gleichen Modellen mit Anschluss: „DELL G3223Q · DP-1“). **★** markiert KDEs primären Monitor.
**✎** benennt ihn um (Enter speichert, leer = zurück zum Modellnamen; gespeichert als `label` in der Konfiguration).
Die kleine Zeile zeigt Anschluss und den internen Alias, der in Feldnamen wie `primary:0` steckt.

**Auf A×B zurück** setzt auf das Raster des **Standardprofils** für diesen Monitor zurück (der Tooltip nennt das
Profil); beim Bearbeiten des Standardprofils selbst auf das Grundraster des Monitors aus der Konfiguration.

## Subgrids {#subgrids}

„In Subgrid teilen“ auf einem leeren Feld teilt es in ein eigenes Raster. Die Subzellen heissen `center:1.0`,
`center:1.1` … und funktionieren wie normale Felder. Über das Schild „⊞ 2×2“ lassen sich Spalten/Zeilen ändern
oder die Teilung aufheben (Charaktere landen dann als Stapel in der ganzen Zelle). Auch die Linien im Subgrid
lassen sich ziehen.

## Überlauf-Felder {#overflow-slots}

Überlauf-Felder werden erst belegt, wenn alle Auffüll-Felder voll sind. Über das Schild „⇊ 1 · max 3“ lassen
sich Reihenfolge und **max. Charaktere** einstellen; das letzte Überlauf-Feld nimmt immer alle übrigen auf.

## Feld-Typen verschieben {#moving-slot-types}

Frei gehaltene Felder (auch Vorschau/Browser/RIFT) direkt ziehen, Überlauf- und Kurzbefehl-Schilder ziehen, ein
Subgrid am Schild „⊞“ ziehen (zieht samt Inhalt um). Auf einem belegten Ziel wird getauscht.

## Speichern {#saving}

Beim Speichern wird die Datei zuerst geprüft und die vorherige Version als `config.yaml.bak` behalten
(siehe [Speichern aus der Web-UI](configuration.md#saving-from-the-web-ui)).
