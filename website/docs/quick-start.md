---
sidebar_position: 3
title: Quick start & CLI
---

# Quick start & CLI reference

## First steps

```bash
fcwm init                # starter config from your monitors (~/.config/fcwm/config.yaml)
fcwm monitors            # output names + work area (without panels)
fcwm windows             # detected EVE clients
fcwm apply -n            # dry run with the default profile
fcwm apply Fleet-Fight   # apply a profile
fcwm watch Solo-Mining   # listener: place new clients automatically when they log in
fcwm watch --initial     # … and place already open clients once at start
fcwm web                 # web UI on http://127.0.0.1:8765/ (includes the listener)
fcwm --lang de apply -n  # output language (de/en)
```

**Hotkeys without fcwm running:** System Settings → Keyboard → Shortcuts → *Add New* → *Command*:
`fcwm apply Fleet-Fight`. With fcwm running you can also define [global hotkeys](hotkeys-appearance.md)
directly in the web UI.

**Autostart:** `systemctl --user enable --now fcwm` (see [Installation](installation.md)).

## Commands

| Command | Description |
|---|---|
| `fcwm monitors` | Show detected monitors (geometry, scale, work area). |
| `fcwm windows [--all]` | Show EVE clients; `--all` lists every window with its window class. |
| `fcwm profiles` | List profiles (`*` marks the default profile). |
| `fcwm apply [PROFILE] [-n]` | Apply a profile (default: `default_profile`); `-n`/`--dry-run` only computes and prints. |
| `fcwm watch [PROFILE] [--initial]` | Listen for new clients and place them automatically. |
| `fcwm web [--host H] [--port N]` | Start the web UI (includes the listener). |
| `fcwm open [--port N]` | Open the web UI in the browser (starts fcwm if needed). |
| `fcwm app [--port N] [--native-frame]` | Open the web UI in its own [app window](web-ui.md#app-window) (starts fcwm if needed; falls back to the browser without PyQt6-WebEngine). |
| `fcwm reload [--port N]` | Make the running instance re-read its config (moves no windows). |
| `fcwm restart [--port N]` | Restart the running instance (systemd service or a manually started `fcwm web`). |
| `fcwm state` | Dump the full state as JSON. |
| `fcwm init [--force]` | Create a starter config from the detected monitors. |
| `fcwm cleanup` | Remove KWin scripts, shortcuts, window rules and color schemes created by fcwm (run before uninstalling). |

`fcwm web` listens on `settings.web.host` / `settings.web.port` from the config (default `127.0.0.1:8765`);
`--host` and `--port` override them. `open`, `reload` and `restart` use the configured port when `--port` is
not given. See [Web UI address](configuration.md#web-ui-address).

### Global options

| Option | Description |
|---|---|
| `-c`, `--config PATH` | Path to `config.yaml` / `.json`. |
| `-b`, `--backend auto\|kwin\|x11` | Force a backend. |
| `-l`, `--lang de\|en` | Output language (default: `settings.language`, otherwise `$LANG`). |
| `-v`, `--verbose` | Debug logging. |
| `-V`, `--version` | Print the version. |

## Config file location

fcwm looks for `$XDG_CONFIG_HOME/fcwm/config.yaml` (usually `~/.config/fcwm/config.yaml`), then for
`config.yaml` in the project folder. `-c PATH` selects a file explicitly – a `.json` file with the same
structure works as well.

## Reload and restart

Both are also available as buttons on the web UI's **Settings** page.

```bash
fcwm reload     # running instance re-reads config.yaml (e.g. after editing by hand) – moves no windows
fcwm restart    # restarts the running instance
```
