# FleetCommander (fcwm)

🇩🇪 [Deutsche Version](README.de.md)

Arranges EVE Online clients on KDE Plasma (Wayland **and** X11) using a grid per monitor.
Profiles define which character goes into which slot. Control it from the CLI, a KDE shortcut or the web UI.

## Dependencies

| What | Purpose | Arch | Debian/Ubuntu |
|---|---|---|---|
| Python ≥ 3.10 | Runtime | `python` | `python3` |
| PyYAML | YAML configuration (not needed for JSON) | `python-yaml` | `python3-yaml` |
| `kscreen-doctor` | Detect monitors (fallback when KWin doesn't answer) | `kscreen` | `kscreen` |
| `busctl`, `journalctl` | D-Bus calls to KWin and reading return values (systemd, usually present) | `systemd` | `systemd` |
| *optional* ruamel.yaml | Keep comments in config.yaml when saving from the web UI | `python-ruamel-yaml` | `python3-ruamel.yaml` |
| *optional* `wmctrl` / `xdotool` / `xrandr` | X11 backend without KWin | `wmctrl xdotool xorg-xrandr` | `wmctrl xdotool x11-xserver-utils` |

On Plasma you only need Python and PyYAML. The web UI uses only the standard library.

## Installation (Arch Linux)

fcwm is distributed as one Arch package (PKGBUILD in `packaging/arch/`):

```bash
git clone https://github.com/jfschubert/FleetCommander.git
cd FleetCommander/packaging/arch
makepkg -si                                   # builds, runs the tests, installs
fcwm init                                    # starter config from your monitors -> ~/.config/fcwm/config.yaml
systemctl --user enable --now fcwm           # runs with your Plasma session
```

The web UI is at http://127.0.0.1:8765/ or via "FleetCommander" in the application menu (`fcwm open`).

The package installs `/usr/bin/fcwm`, the systemd user service `fcwm.service`, the menu entry and the docs
(`/usr/share/doc/fcwm/`, including `config.example.yaml` with all features). **Before uninstalling**, as your user:

```bash
systemctl --user disable --now fcwm
fcwm cleanup        # removes fcwm's KWin window rules, color schemes and global shortcuts
sudo pacman -R fcwm
```

Your config in `~/.config/fcwm/` is kept.

**Coming from `evewm`** (the previous name): the package replaces it. On first start `~/.config/evewm` is
copied to `~/.config/fcwm` (the old folder stays as a backup) and old `evewm-*` window rules and shortcuts are
cleaned up. Switch the service: `systemctl --user disable --now evewm; systemctl --user enable --now fcwm`.

**Reload / restart** (also as buttons in the web UI, "Configuration" window):

```bash
fcwm reload     # running instance re-reads config.yaml (e.g. after editing by hand) – moves no windows
fcwm restart    # restarts the running instance (systemd service or a manually started `fcwm web`)
```

**Updating:** `git pull && cd packaging/arch && makepkg -sif`, then `fcwm restart`. Tested with Plasma 6.7 / KWin 6.7 (Wayland). fcwm only arranges,
switches and previews windows – it never sends input to clients (same category as EVE-O Preview).

## Quick start

```bash
fcwm monitors                 # output names + work area (without panels)
fcwm windows             # detected EVE clients
fcwm apply -n            # dry run with the default profile
fcwm apply Fleet-Fight   # apply a profile
fcwm watch Solo-Mining   # listener: place new clients automatically when they log in
fcwm watch --initial     # … and place already open clients once at start
fcwm web                 # web UI on http://127.0.0.1:8765/ (includes the listener)
fcwm --lang de apply -n  # output language (de/en)
```

**Hotkeys:** System Settings → Keyboard → Shortcuts → *Add New* → *Command*:
`fcwm apply Fleet-Fight`.

**Autostart:** `systemctl --user enable --now fcwm` (see Installation).

## Listener & auto placement

- Event-driven under KWin: a permanently loaded KWin script (`fcwm_listener`) reports
  `windowAdded` / `captionChanged` / `windowRemoved`; Python follows the journal (`journalctl -f`).
  Without KWin (X11) the window list is compared every 2 s.
- A client counts as logged in as soon as its title changes from the start window "EVE" to "EVE - Name".
- **Several simultaneous logins** are collected (1 s of quiet, at most 4 s) and placed in one go.
  Clients that are already placed are not moved and keep their slot – an alt logging in later takes
  the next *free* slot instead of pushing others out.
- In the web UI: "Auto placement" checkbox (header or sidebar) and profile choice. The state is stored
  in `fcwm-state.json` next to the configuration and survives restarts. Even with auto placement off,
  logins appear as notifications and in the event log.
- On exit (Ctrl+C/SIGTERM) the KWin script is unloaded again.

## Hotkeys, locking, title bars

All configurable in the web UI; requires KWin (Plasma) and works while `fcwm web` or `fcwm watch` runs.

- **Hotkeys** ("Hotkeys" window): next / previous layout, cycle the active stack. Per profile its own hotkey
  ("Hotkey" field next to the name) and per slot a stack hotkey (⌨ on the slot). Click a field, press the
  combination; Del clears, Esc cancels. These are real global KDE shortcuts (visible in System Settings under
  KWin). Switching layouts also makes it the **active layout** (▸ in the tab) – used by auto placement and
  stack hotkeys.
- **Cycling a stack:** brings the bottom client of the stack to the front and activates it – pressing
  repeatedly goes through all of them. The "active stack" is the stack of the currently active EVE window.
- **Lock** (header): EVE clients snap straight back to their place after moving, resizing, maximizing or
  tiling. Turning it on locks them where they currently are; every apply (button, hotkey, auto placement)
  updates the positions.
- **Title bars:** hide and/or color them for all EVE clients, plus a color per character. Implemented as our
  own KWin window rules (`fcwm-…` in `~/.config/kwinrulesrc`, other rules are left alone) and small color
  schemes in `~/.local/share/color-schemes/FCWM-*.colors`. Works even when the tool isn't running.
  **Hiding/showing title bars realigns the clients** – otherwise the frame shrinks and leaves a gap at the top.
- **Separator between clients** ("Title bars" window): width in pixels and color. The grid leaves a gap of that
  width; lines are drawn only where two windows meet – one line per edge, none at the outer border or next
  to empty slots. The lines are click-through KWin overlays that behave like background: a line hides as soon
  as a window lying *above* its two neighbors covers the gap (e.g. the focused browser), and when one side has
  no visible client. Optionally only while an EVE client (or a window from a kept-free slot) is active.

```yaml
hotkeys:
  next_profile: Meta+Ctrl+PgDown
  prev_profile: Meta+Ctrl+PgUp
  cycle_stack: Meta+Ctrl+Tab
settings:
  titlebar: {hide: false, color: "#2a6f97"}
  separator: {width: 2, color: "#3c3c3c"}
characters:
  "Alt 1": {color: "#b42828"}
profiles:
  Fleet-Fight:
    hotkey: Meta+Ctrl+2
    stack_hotkeys: {"center:1": Meta+Ctrl+Q}
```

## Language

Web UI: Deutsch/English selector in the top right (remembered by the browser). CLI: `--lang`, otherwise
`settings.language` in the configuration, otherwise `$LANG`.

## Web UI / profile editor

`fcwm web` → http://127.0.0.1:8765/

- **Drag & drop:** drag characters from the palette onto a slot. Dropping onto an occupied slot
  **stacks** (the new one goes on top); hold **Shift** to swap the two instead. Dragging back onto the
  palette removes the assignment.
- **Stacks:** several characters share exactly the same spot. The slot shows the list, top = visible;
  ▲ moves an entry to the top, single entries can be dragged out again. When applying, the tool raises
  the windows so the top entry ends up in front. ⇥/⤓ apply to the whole stack.
- **Extra clients are always stacked:** once all fill slots are taken, further clients are stacked onto
  those slots in turn (disable with `stack_overflow: false` in the profile). Dropping onto an
  automatically filled slot pins the client there and stacks on top of it.
- **Move grid lines:** drag the lines between columns/rows in the preview with the mouse (◆ handle).
  A tooltip shows percent and pixels of both sides, **Shift** snaps to 1/12, each side stays at least
  5 % wide. **Vertical lines are per row:** dragging a segment changes only that row (e.g. row 1 = 50:50,
  row 2 = 75:25); with **Ctrl** the line moves across all rows. Stored as `col_weights`/`row_weights` or
  `row_col_weights: {1: [75, 25]}`; "even lines" on the monitor card resets them. If the
  number of columns or rows changes, the lines of that axis become even again.
- **Subgrids (smaller clients):** ⊞ on an empty slot splits it into its own grid (2×2 by default).
  The sub-cells are called `center:1.0`, `center:1.1` … and work like normal slots: assign, stack,
  keep free, auto-fill. The "⊞ 2×2" tag lets you change columns/rows or merge the cell again
  (characters then end up as a stack in the whole cell). Subgrid lines can be dragged too. In the configuration:
  ```yaml
  subgrids:
    "center:1": "2x2"
  assign:
    "Scout Alt": "center:1.3"
  ```
- **Overflow slots:** ⇊ on an empty slot. Overflow slots are not filled normally; once all fill slots are
  taken, further clients go there in order (as a stack). The "⇊ 1 · max 3" tag sets order and **max
  characters** – the last overflow slot always takes all remaining clients and therefore has no maximum.
  Without overflow slots, extra clients are stacked in turn as before.
  ```yaml
  overflow: [{cell: "right:2", max: 3}, "right:3"]
  ```
- **Keep slots free** (e.g. for a browser or RIFT): ⊘ on an empty slot. The slot never receives EVE
  clients, not even when filling or stacking. Optionally assign a window (title or window class from the
  list, or a regex pattern like `RIFT|Brave`): it is moved into the slot when the profile is applied.
  ✎ or double-click edits, ✕ releases the slot again. In the configuration:
  ```yaml
  blocked:
    "right:3": {label: RIFT, match: "RIFT"}
    "left:3": Browser          # just keep free
  ```
- **Preview slots (like EVE-O Preview):** in a kept-free slot (⊘ → ✎) choose "Preview": *all clients* or
  *hidden only* (behind others in a stack, or minimized). The slot shows live images of the clients as tiles
  with character names (in the title bar color); the active one is highlighted and a click switches to the
  client. Rendered by KWin itself (`WindowThumbnail`), no screen capture.
  **Visible:** *always* (default, like EVE-O Preview – then also on top of other programs) or *only while an
  EVE client is active*. Only while `fcwm web`/`watch` runs.
- **Preview strip on a stack:** ▣ on a slot. A strip of live images along one edge of the stack
  (bottom/top/left/right, size in %), showing *the other (hidden) clients of this stack* or *all clients*.
  "Hidden" disappears by itself when nothing is hidden.
  ```yaml
  blocked:
    "right:3": {label: Alts, preview: hidden, show: eve}   # preview: all|hidden, show: always|eve
  stack_previews:
    "center:0": {mode: stack, edge: right, size: 20}        # mode: stack|all
  ```
- **Move slot types:** drag kept-free slots (also preview/browser/RIFT) directly, drag the overflow and hotkey
  tags, drag a subgrid by its "⊞" tag (moves with its contents). On an occupied target they swap.
- **Don't use monitors:** "Use monitor" checkbox on the monitor card, or `disabled_monitors: [left, right]`
  in the profile. The monitor gets no slots, is skipped when filling and shown hatched in the preview.
  Assignments to it are kept and are filled onto the remaining monitors in the meantime.
- **Slot tools** (on hover): ⇥ / ⤓ span several columns/rows (clicking past the edge resets),
  pin icon: pin an automatically placed client where it is, ✕ remove.
- **Grid per monitor** via the cards below the preview (columns/rows ±, "fill free slots").
  When changing it, assignments keep their column/row as long as it still exists in the new grid.
- **Profiles:** ＋ (new), Duplicate, Rename (name field), Set default (★), Delete.
  Unsaved profiles are marked with ◆. *Apply* also uses unsaved changes.
- Characters that aren't logged in can be planned via "Add character".
- Windows can be collapsed with `—` or by double-clicking the title bar.

Before saving, the file is validated; the previous version is kept as `config.yaml.bak`.
With **ruamel.yaml** installed, comments and formatting outside the edited profile are preserved.
Without ruamel.yaml, PyYAML rewrites the file and the comments are lost.

## Structure

```
fcwm/
  geometry.py      Rect, Insets, GridSpec, grid calculation (pure math, tested)
  monitors.py      monitor detection via kscreen-doctor (fallback xrandr)
  config.py        load + validate YAML/JSON, edit/write back profiles
  layout.py        filter EVE windows, profile -> concrete placements, stacks
  backends/
    kwin.py        Wayland + X11: KWin JS script via D-Bus, reply via the journal
    x11.py         wmctrl / xdotool (X11 only)
  app.py           shared logic for CLI and web (apply, preview, state)
  autoplace.py     listener thread, debounce/batch placement, hotkeys, locking, events (SSE)
  titlebar.py      title bars via KWin window rules
  separators.py    separator lines between clients (KWin QML overlay)
  previews.py      preview slots with live images (KWin QML, WindowThumbnail)
  i18n.py          messages DE/EN
  cli.py, web.py   front ends
  maintenance.py   fcwm init / open / cleanup
packaging/         systemd service, menu entry, arch/PKGBUILD
  static/index.html
```

## Grid calculation

1. **Monitor area:** logical coordinates (rotation and scaling already applied).
2. **Panel deduction** (`reserve`): `auto` uses the KWin work area (`MaximizeArea`, i.e. without
   taskbars), or manually `{top, right, bottom, left}`.
3. **Padding** per monitor, then the **grid** `cols x rows` with optional `col_weights`/`row_weights`
   and `gap`. Edges are rounded cumulatively so no pixels are lost.
4. **Decoration:** KWin sets the frame geometry (including the title bar), so nothing is deducted.
   The X11 backend sets the client geometry, so `settings.decoration` is deducted there.

Slots are numbered row by row (`0` = top left). `span: [columns, rows]` merges cells.
Assigned characters that aren't open keep their slot free. All other clients fill the free slots of
the monitors listed under `fill` alphabetically; after that they are stacked in turn.

## Notes / limitations

- The KWin backend writes a few lines to the user journal per query or window event (the script's return channel).
- The web UI listens on `127.0.0.1` only. It can move windows and overwrite the configuration.
- Tests: `python3 -m unittest discover -s tests`

## License

GPL-3.0 – see [LICENSE](LICENSE).
