---
sidebar_position: 12
title: Kurzbefehle, Fixieren, Titelleisten
---

# Kurzbefehle, Fixieren, Titelleisten, Trennlinien

Alles in der Web-UI einstellbar (meist auf der Seite **Einstellungen**). Benötigt KWin (Plasma) und läuft,
solange `fcwm web` oder `fcwm watch` aktiv ist – ausser den Titelleisten, die auch ohne fcwm wirken.

![Die Einstellungen-Seite](/img/screenshots/settings-de.png)

## Kurzbefehle {#hotkeys}

```yaml
hotkeys:
  next_profile: Meta+Ctrl+PgDown
  prev_profile: Meta+Ctrl+PgUp
  cycle_stack: Meta+Ctrl+Tab
profiles:
  Fleet-Fight:
    hotkey: Meta+Ctrl+2
    stack_hotkeys: {"center:1": Meta+Ctrl+Q, "right:2": Meta+Ctrl+C}
```

- **Global:** nächstes / vorheriges Layout, aktiven Stapel durchschalten (Seite Einstellungen).
- **Pro Profil:** ein eigener Kurzbefehl (unter „Weitere Profil-Optionen“).
- **Pro Feld:** ein Stapel-Kurzbefehl (⚙ → Kurzbefehl für dieses Feld (Stapel durchschalten)).

Feld anklicken, Kombination drücken; **Entf** löscht, **Esc** bricht ab. Es sind echte globale KDE-Kurzbefehle
(in den Systemeinstellungen unter KWin sichtbar). Ein Layout-Wechsel macht das Layout gleichzeitig zum
**aktiven Layout** (▸ im Tab) – das nutzen Auto-Platzierung und Stapel-Kurzbefehle.

### Stapel durchschalten {#cycling-a-stack}

Holt das unterste Fenster des Stapels nach vorn und aktiviert es – mehrfach drücken geht reihum durch alle.
„Aktiver Stapel“ (für `cycle_stack`) ist der Stapel des gerade aktiven Fensters.

Das funktioniert für Stapel aus EVE-Clients **und** für [Fensterstapel](window-zones.md#window-stacks) in frei
gehaltenen Feldern (`stack: true`, Auffangfeld).

## Fixieren {#lock}

**Fixieren** (Kopfzeile): EVE-Clients springen nach Verschieben, Grössenänderung, Maximieren oder Kacheln sofort
an ihren Platz zurück. Beim Einschalten werden sie dort fixiert, wo sie gerade sind; jedes Anwenden (Knopf,
Kurzbefehl, Auto-Platzierung) aktualisiert die Plätze.

## Titelleisten {#title-bars}

```yaml
settings:
  titlebar: {hide: true}
```

Titelleisten aller EVE-Clients ausblenden. Umgesetzt über eigene KWin-Fensterregeln (`fcwm-…` in
`~/.config/kwinrulesrc` – andere Regeln bleiben unberührt). Wirkt auch, wenn fcwm nicht läuft.

**Beim Aus-/Einblenden werden die Clients neu ausgerichtet** – ohne Titelleiste schrumpft sonst der Rahmen und
oben bleibt eine Lücke.

## Trennlinien {#separators}

```yaml
settings:
  separator: {width: 2, color: "#3c3c3c", show: always}   # show: always | eve
```

Breite in Pixel und Farbe einer Linie zwischen Clients. Das Raster lässt dafür eine Lücke dieser Breite;
gezeichnet wird nur dort, wo zwei Fenster aneinanderstossen – eine Linie pro Kante, nicht am Rand und nicht
neben leeren Feldern.

Die Linien sind klickdurchlässige KWin-Overlays, die sich wie Hintergrund verhalten: Eine Linie verschwindet,
sobald ein Fenster, das *über* ihren beiden Nachbarn liegt, die Lücke überdeckt (z. B. der fokussierte Browser),
und wenn auf einer Seite kein sichtbarer Client steht. Mit `show: eve` erscheinen sie nur, solange ein
EVE-Client (oder ein Fenster aus einem frei gehaltenen Feld) aktiv ist.

## Sprache {#language}

Web-UI: Sprachauswahl unter Einstellungen → Allgemein (wird im Browser gespeichert; listet jede [vorhandene Übersetzung](translations.md)). CLI: `--lang`, sonst
`settings.language`, sonst `$LANG`.
