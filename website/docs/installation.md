---
sidebar_position: 2
title: Installation
---

# Installation

## Dependencies

| What | Purpose | Arch | Debian/Ubuntu |
|---|---|---|---|
| Python ≥ 3.10 | Runtime | `python` | `python3` |
| PyYAML | YAML configuration (not needed for JSON) | `python-yaml` | `python3-yaml` |
| `kscreen-doctor` | Detect monitors (fallback when KWin doesn't answer) | `kscreen` | `libkscreen-bin` |
| `busctl`, `journalctl` | D-Bus calls to KWin and reading return values (systemd, usually present) | `systemd` | `systemd` |
| *optional* ruamel.yaml | Keep comments in `config.yaml` when saving from the web UI | `python-ruamel-yaml` | `python3-ruamel.yaml` |
| PyQt6-WebEngine | [App window](web-ui.md#app-window) instead of a browser tab (installed with the fcwm packages; without it `fcwm app` opens the browser) | `python-pyqt6-webengine` | `python3-pyqt6.qtwebengine` |
| *optional* `wmctrl` / `xdotool` / `xrandr` | X11 backend without KWin | `wmctrl xdotool xorg-xrandr` | `wmctrl xdotool x11-xserver-utils` |

On Plasma you only need Python and PyYAML. The web UI uses only the Python standard library.

## Arch Linux

fcwm is distributed as one Arch package (PKGBUILD in `packaging/arch/`):

```bash
git clone https://github.com/jfschubert/FleetCommander.git
cd FleetCommander/packaging/arch
makepkg -si                          # builds, runs the tests, installs
fcwm init                            # starter config from your monitors -> ~/.config/fcwm/config.yaml
systemctl --user enable --now fcwm   # runs with your Plasma session
```

The web UI is at <http://127.0.0.1:8765/> (or the [configured port](configuration.md#web-ui-address)),
or via "FleetCommander" in the application menu, which opens it in its own [app window](web-ui.md#app-window) (`fcwm app`).

The package installs `/usr/bin/fcwm`, the systemd user service `fcwm.service`, the menu entry and the docs
(`/usr/share/doc/fcwm/`, including `config.example.yaml` with all features).

### Updating

```bash
git pull && cd packaging/arch && makepkg -sif
fcwm restart
```

### Uninstalling

**Before uninstalling**, as your normal user:

```bash
systemctl --user disable --now fcwm
fcwm cleanup        # removes fcwm's KWin window rules, color schemes and global shortcuts
sudo pacman -R fcwm
```

Your config in `~/.config/fcwm/` is kept.

## Other distributions

Packages for **Debian/Ubuntu** and **Fedora/openSUSE** are being added under `packaging/` in the repository.
See [`packaging/README`](https://github.com/jfschubert/FleetCommander/blob/main/packaging/README.md) there for the current state and build instructions.

Until then you can run fcwm straight from a checkout: install the dependencies from the table above and use
`./fcwm.sh` (or `python3 -m fcwm`) from the repository root.

## Coming from `evewm`

`evewm` is the previous name; the package replaces it. On first start `~/.config/evewm` is copied to
`~/.config/fcwm` (the old folder stays as a backup) and old `evewm-*` window rules and shortcuts are cleaned
up. Switch the service:

```bash
systemctl --user disable --now evewm
systemctl --user enable --now fcwm
```
