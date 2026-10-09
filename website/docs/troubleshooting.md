---
sidebar_position: 21
title: Troubleshooting & limitations
---

# Troubleshooting & limitations

## Common checks

- **Debug info:** *Settings → Debug info* in the web UI shows the backend, listener, versions, paths and every
  detected EVE client and monitor. The copy button (⧉) puts it on the clipboard as text – please attach it to
  bug reports.
- **No clients found:** `fcwm windows --all` lists every window with its class and title. Adjust
  `settings.match.caption_regex` / `resource_class` if your launcher names windows differently.
- **Wrong monitor:** `fcwm monitors` shows output names; use them as `output:` in `monitors`.
- **Plan looks wrong:** `fcwm apply -n` prints the computed placements without moving anything; add `-v`
  for debug output.
- **Changes to `config.yaml` by hand:** run `fcwm reload` (moves no windows).
- **Web UI not reachable:** check the [configured host/port](configuration.md#web-ui-address) and whether the
  service runs: `systemctl --user status fcwm`.
- **Popups end up in the catch-all zone:** add them to `exclude` (see [Window zones](window-zones.md#catch-all-zone)).
  Transient dialogs are never moved.
- **Leftover window rules / shortcuts:** `fcwm cleanup` removes everything fcwm created in KWin
  (stop the service first).

## Limitations

- Hotkeys, lock, separators and previews need **KWin** (Plasma) and a running `fcwm web` / `fcwm watch`.
  The X11 backend (`wmctrl`/`xdotool`) only arranges windows.
- The KWin backend writes a few lines to the user journal per query or window event (the KWin script's
  return channel).
- The web UI has no authentication. It listens on `127.0.0.1` by default; it can move windows and overwrite the
  configuration – don't expose it to the network.
- Without ruamel.yaml, saving from the web UI loses the comments in `config.yaml`.
- fcwm never sends input to EVE clients; it only arranges, switches and previews windows.
