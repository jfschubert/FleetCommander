---
sidebar_position: 12
title: Hotkeys, lock, title bars
---

# Hotkeys, lock, title bars, separators

All of this is configurable in the web UI (mostly on the **Settings** page). It requires KWin (Plasma) and
works while `fcwm web` or `fcwm watch` runs – except title bars, which keep working without fcwm.

## Hotkeys

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

- **Global:** next / previous layout, cycle the active stack (Settings page).
- **Per profile:** its own hotkey (under "More profile options").
- **Per slot:** a stack hotkey (⚙ → Hotkey for this slot (cycle stack)).

Click a field and press the combination; **Del** clears, **Esc** cancels. These are real global KDE shortcuts
(visible in System Settings under KWin). Switching layouts also makes it the **active layout** (▸ in the tab),
which is used by auto placement and stack hotkeys.

### Cycling a stack

Brings the bottom window of the stack to the front and activates it – pressing repeatedly goes through all of
them. The "active stack" (for `cycle_stack`) is the stack of the currently active window.

This works for stacks of EVE clients **and** for [window stacks](window-zones.md#window-stacks) in kept-free
slots (`stack: true`, catch-all).

## Lock

**Lock** (header): EVE clients snap straight back to their place after moving, resizing, maximizing or tiling.
Turning it on locks them where they currently are; every apply (button, hotkey, auto placement) updates the
positions.

## Title bars

```yaml
settings:
  titlebar: {hide: false, color: "#2a6f97"}
characters:
  "Alt 1": {color: "#b42828"}
```

Hide and/or color the title bars of all EVE clients, plus a color per character. Implemented as fcwm's own KWin
window rules (`fcwm-…` in `~/.config/kwinrulesrc` – other rules are left alone) and small color schemes in
`~/.local/share/color-schemes/FCWM-*.colors`. Works even when fcwm isn't running.

**Hiding/showing title bars realigns the clients** – otherwise the frame shrinks and leaves a gap at the top.

## Separators

```yaml
settings:
  separator: {width: 2, color: "#3c3c3c", show: always}   # show: always | eve
```

Width in pixels and color of a line between clients. The grid leaves a gap of that width; lines are drawn only
where two windows meet – one line per edge, none at the outer border or next to empty slots.

The lines are click-through KWin overlays that behave like background: a line hides as soon as a window lying
*above* its two neighbors covers the gap (e.g. the focused browser), and when one side has no visible client.
With `show: eve` they are only shown while an EVE client (or a window from a kept-free slot) is active.

## Language

Web UI: language selector under Settings → General (remembered by the browser; lists every [available translation](translations.md)). CLI: `--lang`, otherwise
`settings.language`, otherwise `$LANG`.
