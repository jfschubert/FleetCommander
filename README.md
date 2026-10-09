<img src="fcwm/static/fcwm.svg" alt="FleetCommander" width="96" align="right">

# FleetCommander (fcwm)

🇩🇪 [Deutsche Version](README.de.md) · 📖 **[Documentation](https://jfschubert.github.io/FleetCommander/)**

Arranges EVE Online clients on KDE Plasma (Wayland **and** X11) using a grid per monitor.
Profiles define which character goes into which slot. Control it from the CLI, a KDE shortcut or the web UI.

fcwm only arranges, switches and previews windows – it never sends input to clients (same category as
EVE-O Preview). Tested with Plasma 6.7 / KWin 6.7 (Wayland).

## Features

- **Per-monitor grids** with draggable grid lines, spans and nested **subgrids** for smaller clients
- **Profiles** with character assignments, automatic filling, **stacks** and **overflow** slots
- **Auto placement**: clients are placed as soon as they log in (simultaneous logins are batched)
- **Window zones**: keep slots free for a browser, RIFT, an editor … – stack matching windows there or
  catch every newly opened window in one slot
- **Global hotkeys** for switching layouts and cycling stacks, **lock** windows in place
- **Live previews** like EVE-O Preview, rendered by KWin (no screen capture)
- Colored / hidden **title bars** per character and **separator lines** between clients
- **Web UI** with a drag & drop profile editor (English / German)

## Install (Arch Linux)

```bash
git clone https://github.com/jfschubert/FleetCommander.git
cd FleetCommander/packaging/arch
makepkg -si                          # builds, runs the tests, installs
fcwm init                            # starter config -> ~/.config/fcwm/config.yaml
systemctl --user enable --now fcwm   # runs with your Plasma session
```

Packages for other distributions: see [`packaging/README.md`](packaging/README.md).
Dependencies, updating and uninstalling: [Installation](https://jfschubert.github.io/FleetCommander/installation/).

## Quick start

```bash
fcwm monitors            # output names + work area
fcwm windows             # detected EVE clients
fcwm apply -n            # dry run with the default profile
fcwm apply Fleet-Fight   # apply a profile
fcwm watch --initial     # place clients automatically when they log in
fcwm web                 # web UI on http://127.0.0.1:8765/ (includes the listener)
```

The full CLI and configuration reference, the web UI guide and more are in the
**[documentation](https://jfschubert.github.io/FleetCommander/)** (sources in [`website/`](website/)).

Tests: `python3 -m unittest discover -s tests`

Want to translate fcwm into your language? See [Translations](https://jfschubert.github.io/FleetCommander/translations/).

## License

GPL-3.0 – see [LICENSE](LICENSE). The app icon is original artwork of this project; UI icons are from [Lucide](https://lucide.dev) (ISC).

EVE Online® and Fenris Creations™ and all related logos and other elements are trademarks of Fenris Creations
(formerly CCP Games). FleetCommander is an unofficial third-party tool and is not affiliated with, endorsed or
approved by Fenris Creations. Details: [NOTICE](NOTICE).
