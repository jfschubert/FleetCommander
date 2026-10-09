---
sidebar_position: 11
title: Auto placement & listener
---

# Auto placement & listener

`fcwm web` and `fcwm watch` run a listener that notices new and changed windows and places EVE clients as soon
as they log in.

## How it works

- **Event-driven under KWin:** a permanently loaded KWin script (`fcwm_listener`) reports
  `windowAdded` / `captionChanged` / `windowRemoved`; Python follows the journal (`journalctl -f`).
  Without KWin (X11 backend) the window list is compared every 2 s.
- A client counts as **logged in** as soon as its title changes from the start window "EVE" to "EVE - Name".
- **Several simultaneous logins** are collected (1 s of quiet, at most 4 s) and placed in one go.
- Clients that are already placed are not moved and keep their slot – an alt logging in later takes the next
  *free* slot instead of pushing others out.
- On exit (Ctrl+C / SIGTERM) the KWin script is unloaded again.

## Turning it on

- **Web UI:** "Auto placement" checkbox and profile choice. The state is stored in `fcwm-state.json` next to the
  configuration and survives restarts. Even with auto placement off, logins appear as notifications and in
  the event log.
- **CLI:** `fcwm watch [PROFILE]`; `--initial` also places already open clients once at start.

The profile used is the **active layout** (▸ in the profile tab). Switching layouts by hotkey or applying a
profile makes it the active layout.

## Other windows

With auto placement on, the listener also handles non-EVE windows for [window zones](window-zones.md):
windows matching a kept-free slot's `match`, and newly opened windows for a
[catch-all zone](window-zones.md#catch-all-zone).
