---
sidebar_position: 14
title: Fensterzonen
---

# Fensterzonen (frei gehaltene Felder)

Neben EVE-Clients kann fcwm auch die anderen Programme auf deinen Bildschirmen verwalten: Browser, RIFT, Editor,
Chat … Jedes davon lebt in einem **frei gehaltenen Feld** (`blocked` im Profil). Ein frei gehaltenes Feld erhält
nie EVE-Clients, auch nicht beim Auffüllen oder Stapeln.

In der Web-UI legst du es mit ⚙ → **Frei halten / für andere Fenster (Browser, RIFT, Auffang …)** auf einem
leeren Feld an; ⚙ → **Bearbeiten (Name, Fenster, Vorschau)** (oder Doppelklick) ändert es, ⚙ → **Wieder für
Clients freigeben** macht es wieder zu einem normalen Feld. Die Checkboxen im Editor entsprechen den Schlüsseln
unten: „Alle passenden Fenster stapeln“ (`stack`), „Auffang-Feld für neue Fenster“ mit „Nicht einfangen
(Titel/Klasse, Regex)“ (`catch_all`, `exclude`) und „Fenstergrösse beibehalten“ (`resize: false`).

![Frei gehaltene Felder für Browser und RIFT (schraffiert)](/img/screenshots/layout-de.png)

## Nur frei halten {#just-keep-free}

```yaml
blocked:
  "left:3": Browser          # nur Beschriftung
```

Das Feld bleibt leer – praktisch für ein Fenster, das du selbst platzierst.

## Ein Fenster pro Feld {#one-window-per-slot}

```yaml
blocked:
  "right:3": {label: RIFT, match: "RIFT|Brave"}
```

`match` ist ein **Regex ohne Unterscheidung von Gross-/Kleinschreibung**, geprüft gegen **Titel oder
Fensterklasse** von Nicht-EVE-Fenstern (die Web-UI bietet Titel und Klassen offener Fenster zur Auswahl an).
Fenster der EVE-Fensterklasse (auch die „EVE“-Fenster vor dem Login) und transiente Fenster (Dialoge) werden nie
erfasst.
Beim Anwenden des Profils – und bei eingeschalteter [Auto-Platzierung](auto-placement.md), sobald ein passendes
Fenster erscheint – wird das **erste** passende Fenster in das Feld verschoben.

## Fensterstapel {#window-stacks}

```yaml
blocked:
  "right:2": {label: Code, match: "code", stack: true}
```

Mit `stack: true` landen **alle** passenden Fenster als Stapel in diesem Feld (erster Treffer oben) statt nur
des ersten.

Fensterstapel lassen sich wie EVE-Stapel durchschalten:

- mit einem Stapel-Kurzbefehl auf dem Feld: `stack_hotkeys: {"right:2": Meta+Ctrl+C}`,
- mit dem globalen Kurzbefehl **Stapel durchschalten**, wenn ein Fenster dieses Stapels aktiv ist.

## Auffangfeld {#catch-all-zone}

```yaml
blocked:
  "left:3": {label: Neue Fenster, catch_all: true, resize: false, exclude: "firefox|dolphin"}
```

Solange fcwm mit **eingeschalteter Auto-Platzierung** läuft, wird jedes **neu geöffnete** normale Fenster, das

- kein EVE-Client ist (kein Fenster der EVE-Fensterklasse, auch nicht die „EVE“-Fenster vor dem Login),
- nicht zum `match` eines anderen Feldes passt und
- kein transientes Fenster (Dialog) ist,

in das Auffangfeld verschoben (gestapelt). Regeln:

- **Bestehende Fenster bleiben unberührt** – nur Fenster, die geöffnet werden, nachdem fcwm zu beobachten begann.
- **Dialoge und Popups, die zu einem Elternfenster gehören** (transiente Fenster in KWin), werden nie
  verschoben – Popups eines Programms erscheinen also dort, wo das Programm sie hinsetzt.
- `exclude` ist ein optionaler Regex (Titel oder Klasse, ohne Gross-/Kleinschreibung) für Fenster, die das
  Auffangfeld ignorieren soll.
- Nur das **erste** Auffangfeld eines Profils wird verwendet.

## Fenstergrösse behalten {#keep-the-windows-size}

```yaml
blocked:
  "left:3": {label: Neue Fenster, catch_all: true, resize: false}
  "right:3": {label: Nachrichten, match: "telegram", resize: false}
```

`resize: false` behält die eigene Grösse des Fensters, begrenzt auf das Feld und darin zentriert. So werden
kleine Fehler- oder Meldungsdialoge nicht auf die volle Feldgrösse aufgeblasen. Funktioniert für Auffangfelder
und `match`-Felder gleichermassen.

## Optionen im Überblick {#options-at-a-glance}

| Schlüssel | Standard | Beschreibung |
|---|---|---|
| `label` | – | In der Web-UI angezeigter Name. |
| `match` | – | Regex (Titel oder Klasse, ohne Gross-/Kleinschreibung) der Fenster, die hierher gehören. |
| `stack` | `false` | Alle passenden Fenster als Stapel hier ablegen (erster Treffer oben). |
| `catch_all` | `false` | Neu geöffnete Fenster auffangen, die zu keinem anderen Feld passen. |
| `exclude` | – | Regex der Fenster, die das Auffangfeld ignoriert. |
| `resize` | `true` | `false`: Fenstergrösse behalten (auf das Feld begrenzt, zentriert). |
| `preview` / `show` | – | Macht das Feld stattdessen zum [Vorschau-Feld](previews.md#preview-slots). |
