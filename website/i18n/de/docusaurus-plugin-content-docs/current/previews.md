---
sidebar_position: 13
title: Vorschauen
sidebar_label: Vorschauen (experimentell)
---

# Live-Vorschauen

:::warning Experimentell / in Arbeit

Vorschauen funktionieren, sind aber noch in Entwicklung: Verhalten, Optionen und Konfigurationsformat können
sich ändern, und es gibt noch Ecken und Kanten (z. B. hält KWin die Vorschaufenster immer im Vordergrund).
Rückmeldungen über [GitHub-Issues](https://github.com/jfschubert/FleetCommander/issues) sind willkommen.

:::

fcwm kann Live-Bilder deiner Clients zeigen, wie EVE-O Preview. Gerendert werden sie von KWin selbst
(`WindowThumbnail`) – ohne Bildschirmaufnahme – und nur, solange `fcwm web` / `fcwm watch` läuft.

## Vorschau-Felder {#preview-slots}

![Ein Vorschau-Feld (unten rechts) im Profil Fleet-Fight](/img/screenshots/fleet-fight-de.png)

Ein frei gehaltenes Feld kann zum Vorschau-Feld werden (⚙ → Frei halten / für andere Fenster, dann ⚙ → Bearbeiten (Name, Fenster, Vorschau) → „Vorschau“):

- `preview: all` – alle Clients,
- `preview: hidden` – nur verdeckte Clients (hinten im Stapel bzw. minimiert).

Das Feld zeigt die Clients als Kacheln mit Charakternamen; der aktive ist
hervorgehoben, ein Klick wechselt zum Client.

**Sichtbar** (`show`): `always` (Standard, wie EVE-O Preview – liegt dann auch über anderen Programmen) oder
`eve` (nur solange ein EVE-Client aktiv ist).

```yaml
blocked:
  "right:3": {label: Alts, preview: hidden, show: eve}   # preview: all|hidden, show: always|eve
```

## Vorschau-Leiste auf einem Stapel {#preview-strip-on-a-stack}

⚙ → **Vorschau-Leiste auf diesem Stapel** fügt eine Leiste mit Live-Bildern an einer Kante des Stapels hinzu.

```yaml
stack_previews:
  "center:0": {mode: stack, edge: right, size: 20}   # mode: stack|all
```

| Schlüssel | Werte | Beschreibung |
|---|---|---|
| `mode` | `stack` (Standard), `all` | *Die anderen (verdeckten) Clients dieses Stapels* oder *alle Clients*. `stack` verschwindet von selbst, wenn nichts verdeckt ist. |
| `edge` | `bottom` (Standard), `top`, `left`, `right` | Kante des Stapels. |
| `size` | 5–60, Standard 18 | Grösse in Prozent des Feldes. |
| `show` | `always` (Standard), `eve` | Wie bei Vorschau-Feldern. |
