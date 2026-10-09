---
sidebar_position: 10
title: Web UI
---

# Web UI

Start it with `fcwm web` (or run the systemd service) and open <http://127.0.0.1:8765/> – or use
`fcwm open`, or the [app window](#app-window) via "FleetCommander" in the application menu. Host and port are
[configurable](configuration.md#web-ui-address). The web UI includes the [listener](auto-placement.md).

The language (Deutsch/English) is selected under **Settings → General** and remembered by the browser.

![The layout editor with three monitors](/img/screenshots/layout-en.png)

## App window

Prefer not to deal with a browser tab? `fcwm app` – or simply "FleetCommander" in the application menu – opens
the same web UI in its own window, starting fcwm first if it isn't running yet. There is nothing to
configure: it is exactly the page from the browser (F5 / Ctrl+R reloads). Links to other sites open in your
default browser; "Open in browser" in the menu entry's right-click menu (or `fcwm open`) still gives you the
browser tab. A [catch-all slot](window-zones.md) never grabs this window.

The window uses FleetCommander's **own title bar** instead of KDE's: drag the header to move it, double-click it
to maximize, use **– □ ✕** on the right, and drag the window edges to resize. Moving and resizing is still done
by KWin, so snapping to screen edges keeps working. `fcwm app --native-frame` keeps the KDE title bar.

The window needs **PyQt6-WebEngine** (Arch `python-pyqt6-webengine`, Debian/Ubuntu `python3-pyqt6.qtwebengine`,
Fedora `python3-pyqt6-webengine`, openSUSE `python3-PyQt6-WebEngine`). Without it, `fcwm app` says so and opens
the browser instead.

## Pages

The UI has three pages:

- **Layout** (main page): profiles, the monitor preview with all slots, the character palette, the monitor
  cards, apply, auto placement and lock.
- **Settings**: language, global hotkeys, title bars / separators, debug info (backend,
  versions, clients, monitors – with a copy button for bug reports), the config file with **reload** and
  **restart** buttons, and the web UI host/port (needs a restart).
- **About**: version, links (documentation, GitHub, bug reports, license), credits, the legal notice – and how to
  say thanks with an **ISK donation** in game to *Mister Forever*. The character portrait is loaded from the
  official EVE image server only when the page is opened.

Longer help texts are behind small **i** info icons – hover over them to read the explanation.

## Profiles

＋ creates a new profile; rename it in the name field. The profile **⋯** menu holds **Duplicate**,
**Set default** (★) and **Delete**. Description, focus character and the profile hotkey sit under
**More profile options**. Unsaved profiles are marked with ◆; *Apply* also uses unsaved changes.

## Assigning characters

- **Drag & drop:** drag characters from the palette onto a slot. Dropping onto an occupied slot
  **stacks** (the new one goes on top); hold **Shift** to swap the two instead. Dragging back onto the
  palette removes the assignment.
- **Stacks:** several characters share exactly the same spot. The slot shows the list, top = visible.
  Each stack row has its own buttons: ▲ moves the entry to the top, the pin icon pins it, ✕ removes it.
  Single entries can also be dragged out again. When applying, fcwm raises the windows so the top entry ends
  up in front.
- **Extra clients are always stacked:** once all fill slots are taken, further clients are stacked onto
  those slots in turn (disable with `stack_overflow: false`). Dropping onto an automatically filled slot
  pins the client there and stacks on top of it.
- Characters that aren't logged in can be planned via **Add character**.

## The slot menu (⚙)

![The ⚙ menu of a slot](/img/screenshots/cell-menu-en.png)

Every slot has a gear button **⚙** that opens its action menu. Which entries appear depends on the slot.

**Client slots:**

| Menu entry | Effect |
|---|---|
| Wider (span columns) / Taller (span rows) | Span several columns / rows (clicking past the edge resets). Applies to the whole stack. |
| Pin at this position | Pin an automatically placed client where it is. |
| Hotkey for this slot (cycle stack) | Hotkey that cycles the stack in this slot. |
| Preview strip on this stack | Live preview strip along an edge of the stack – see [Previews](previews.md#preview-strip-on-a-stack). |
| Split cell into a subgrid | Split an empty slot into its own grid (2×2 by default) – see [Subgrids](#subgrids). |
| Use as overflow slot | Make the slot an [overflow slot](configuration.md#overflow). |
| Keep free / for other windows (browser, RIFT, catch-all …) | Turn the slot into a kept-free slot / [window zone](window-zones.md). |
| Remove assignment | Remove the character assignment. |

**Kept-free slots:**

| Menu entry | Effect |
|---|---|
| Edit (name, windows, preview) | Open the slot editor (double-click works too). |
| Hotkey for this slot | Hotkey that cycles the [window stack](window-zones.md#window-stacks) in this slot. |
| Release for clients again | Turn it back into a normal slot. |

### The slot editor

For kept-free slots the editor has a name, the window pattern (pick a title/class of an open window or enter a
regex) and these options – see [Window zones](window-zones.md):

| Option | Config key |
|---|---|
| Stack all matching windows | `stack: true` |
| Catch-all slot for new windows, with the field "Don't catch (title/class, regex)" | `catch_all: true`, `exclude` |
| Keep window size | `resize: false` |
| Preview | `preview`, `show` – see [Previews](previews.md#preview-slots) |

## Grid lines

Drag the lines between columns/rows in the preview (◆ handle). A tooltip shows percent and pixels of both
sides, **Shift** snaps to 1/12, each side stays at least 5 % wide.

**Vertical lines are per row:** dragging a segment changes only that row (e.g. row 1 = 50:50, row 2 = 75:25);
with **Ctrl** the line moves across all rows. Stored as `col_weights`/`row_weights` or
`row_col_weights: {1: [75, 25]}`. "Even lines" on the monitor card resets them. If the number of columns or
rows changes, the lines of that axis become even again.

## Monitor cards

Below the preview, one card per monitor: columns/rows ±, "fill free slots", "even lines" and
**Use monitor** (unchecked = `disabled_monitors`). When the grid changes, assignments keep their column/row as
long as it still exists in the new grid.

Each card shows the monitor's **name**: by default its model from the monitor itself (EDID, e.g. "DELL G3223Q";
identical models get the connector added: "DELL G3223Q · DP-1"). **★** marks KDE's primary monitor. **✎** renames
it (Enter saves, empty = back to the model name; stored as `label` in the config). The small line shows connector
and the internal alias used in slot names like `primary:0`.

**Reset to A×B** goes back to the grid of the **default profile** for that monitor (tooltip shows which profile);
while editing the default profile itself it uses the monitor's base grid from the config.

## Subgrids

"Split into subgrid" on an empty slot splits it into its own grid. The sub-cells are called `center:1.0`,
`center:1.1` … and work like normal slots. The "⊞ 2×2" tag lets you change columns/rows or merge the cell again
(characters then end up as a stack in the whole cell). Subgrid lines can be dragged too.

## Overflow slots

Overflow slots are filled only once all fill slots are taken. The "⇊ 1 · max 3" tag sets order and **max
characters**; the last overflow slot always takes all remaining clients.

## Moving slot types

Drag kept-free slots (also preview/browser/RIFT) directly, drag the overflow and hotkey tags, drag a subgrid by
its "⊞" tag (moves with its contents). On an occupied target they swap.

## Saving

Before saving, the file is validated and the previous version is kept as `config.yaml.bak`
(see [Saving from the web UI](configuration.md#saving-from-the-web-ui)).
