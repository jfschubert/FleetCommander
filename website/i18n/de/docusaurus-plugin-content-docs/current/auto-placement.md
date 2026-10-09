---
sidebar_position: 11
title: Auto-Platzierung & Listener
---

# Auto-Platzierung & Listener

`fcwm web` und `fcwm watch` starten einen Listener, der neue und geänderte Fenster bemerkt und EVE-Clients
platziert, sobald sie sich einloggen.

## So funktioniert es {#how-it-works}

- **Unter KWin ereignisgesteuert:** ein dauerhaft geladenes KWin-Skript (`fcwm_listener`) meldet
  `windowAdded` / `captionChanged` / `windowRemoved`; Python folgt dem Journal (`journalctl -f`).
  Ohne KWin (X11-Backend) wird alle 2 s die Fensterliste verglichen.
- Ein Client gilt als **eingeloggt**, sobald sein Titel vom Startfenster „EVE“ zu „EVE - Name“ wechselt.
- **Mehrere Logins gleichzeitig** werden gesammelt (1 s Ruhe, höchstens 4 s) und in einem Rutsch platziert.
- Bereits platzierte Clients werden nicht bewegt und behalten ihr Feld – ein später einloggender Alt rutscht in
  das nächste *freie* Feld, statt andere zu verdrängen.
- Beim Beenden (Strg+C / SIGTERM) wird das KWin-Skript wieder entladen.

## Einschalten {#turning-it-on}

- **Web-UI:** Checkbox „Auto-Platzierung“ und Profilwahl. Der Zustand liegt in `fcwm-state.json` neben der
  Konfiguration und übersteht Neustarts. Auch bei ausgeschalteter Auto-Platzierung erscheinen Logins als
  Benachrichtigung und im Ereignis-Log.
- **CLI:** `fcwm watch [PROFIL]`; `--initial` platziert beim Start auch bereits offene Clients einmal.

Verwendet wird das **aktive Layout** (▸ im Profil-Tab). Ein Layout-Wechsel per Kurzbefehl oder das Anwenden
eines Profils macht es zum aktiven Layout.

## Andere Fenster {#other-windows}

Bei eingeschalteter Auto-Platzierung kümmert sich der Listener auch um Nicht-EVE-Fenster für
[Fensterzonen](window-zones.md): Fenster, die zum `match` eines frei gehaltenen Feldes passen, und neu geöffnete
Fenster für ein [Auffangfeld](window-zones.md#catch-all-zone).
