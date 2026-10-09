---
sidebar_position: 20
title: Configuration reference
---

# Configuration reference

The configuration lives in `~/.config/fcwm/config.yaml` (see [config file location](quick-start.md#config-file-location)).
`fcwm init` creates a starter file from your monitors; the package also ships a fully commented
`config.example.yaml` in `/usr/share/doc/fcwm/`. Most settings can be edited in the [web UI](web-ui.md).

Top-level keys:

| Key | Description |
|---|---|
| `settings` | Global settings: backend, language, web UI address, client matching, gap, title bars, separators. |
| `monitors` | Monitor aliases with their default grid. |
| `default_profile` | Profile used when none is given. |
| `profiles` | Named layouts. |
| `hotkeys` | Global hotkeys (next/previous layout, cycle stack). |

## settings

```yaml
settings:
  backend: auto            # auto | kwin (Wayland + X11 under Plasma) | x11 (wmctrl/xdotool)
  language: en             # de | en – language of CLI/server messages
  web: {host: 127.0.0.1, port: 8765}
  match:
    caption_regex: '^EVE - (?P<char>.+)$'
    resource_class: '^steam_app_8500$'   # Steam/Proton EVE; leave empty for other launchers
  gap: 0                   # gap between grid cells in pixels
  decoration: {top: 0, right: 0, bottom: 0, left: 0}   # x11 backend only
  min_size: [1024, 768]    # warn when a slot is smaller (EVE minimum)
  titlebar: {hide: false}
  separator: {width: 2, color: "#3c3c3c", show: always}
```

| Key | Default | Description |
|---|---|---|
| `backend` | `auto` | `kwin` works on Wayland and X11 under Plasma; `x11` uses `wmctrl`/`xdotool` without KWin. |
| `language` | `$LANG` | Language code for CLI and server messages (`en`, `de`, or any [added language](translations.md)). The web UI has its own selector (Settings → General, remembered by the browser). The CLI option `--lang` wins. |
| `web.host` | `127.0.0.1` | Listen address of the web UI. |
| `web.port` | `8765` | Port of the web UI. |
| `match.caption_regex` | `^EVE - (?P<char>.+)$` | How EVE clients are recognised; the group `(?P<char>…)` yields the character name. |
| `match.resource_class` | – | Optional regex for the window class (e.g. `^steam_app_8500$` for Steam/Proton). |
| `gap` | `0` | Gap between grid cells in pixels. |
| `decoration` | `0` | Window decoration size. Only used by the `x11` backend, which sets the client geometry; KWin sets the frame geometry, so nothing is deducted there. |
| `min_size` | `[1024, 768]` | Warn when a slot is smaller than this. |
| `titlebar` | `{hide: false}` | Hide the title bars of all EVE clients – see [Title bars](hotkeys-appearance.md#title-bars). |
| `separator` | `{width: 0}` | Separator line between clients: `width` (0–20 px), `color`, `show: always\|eve` – see [Separators](hotkeys-appearance.md#separators). |

### Web UI address

```yaml
settings:
  web: {host: 127.0.0.1, port: 8765}
```

- `fcwm web --host H --port N` overrides both values for one run.
- `fcwm open`, `fcwm reload` and `fcwm restart` talk to the configured port unless `--port` is given.
- The values can also be edited on the web UI's **Settings** page. A change takes effect after a **restart**
  (`fcwm restart` or the restart button).

:::warning Keep it on localhost
The web UI has no authentication. Its API can move windows and rewrite your configuration. Keep the
default `127.0.0.1` and do **not** expose the port to your network or the internet.
:::

## monitors

Monitors get an alias of your choice. They are matched by output name (`fcwm monitors` shows them) or by
`index:` (0 = leftmost).

```yaml
monitors:
  left:
    output: DP-5
    grid: 2x2              # columns x rows – slots row by row: 0 1 / 2 3
    reserve: auto          # panel deduction: auto = KWin work area, or {top, right, bottom, left}
  center:
    output: DP-1
    grid: 1x1
    reserve: auto
    padding: 0             # extra inner margin (number or {top: …, …})
  right:
    index: 2
    grid: 2x2
```

| Key | Description |
|---|---|
| `output` / `index` | Output name (e.g. `DP-1`) or position from the left. |
| `grid` | Default grid: `"2x2"` or `{cols, rows, col_weights, row_weights, row_col_weights}` – see [Grids and weights](#grids-and-weights). |
| `reserve` | `auto` uses the KWin work area (without panels); otherwise `{top, right, bottom, left}` in pixels. |
| `padding` | Extra inner margin: a number or `{top, right, bottom, left}`. |
| `label` | Display name in the web UI. Default: the monitor's model (EDID), with the connector for identical models. |

## profiles

```yaml
default_profile: Solo-Mining

profiles:
  Solo-Mining:
    description: Main big in the center, miners left and right
    hotkey: Meta+Ctrl+1
    assign:
      "Main": center:0
      "Alt 1": left:0
      "Alt 2": {monitor: left, slot: 1, span: [1, 2]}
    fill: [left, right]
    focus: Main
```

| Key | Description |
|---|---|
| `description` | Free text. |
| `grids` | Override monitor grids for this profile: `{left: 1x3, center: {cols: 2, rows: 2, col_weights: [2, 1]}}`. |
| `assign` | Character → slot. See [assign](#assign). |
| `fill` | Monitors whose free slots receive further clients. See [fill](#fill-and-stacking). |
| `stack_overflow` | `true` (default): once all fill slots are taken, further clients are stacked onto them in turn. |
| `focus` | Character to activate at the end. |
| `disabled_monitors` | Monitors not used by this profile. |
| `subgrids` | Split cells into their own grid. See [subgrids](#subgrids). |
| `overflow` | Overflow slots. See [overflow](#overflow). |
| `blocked` | Kept-free slots and window zones. See [blocked](#blocked). |
| `stack_previews` | Preview strips on stacks. See [Previews](previews.md#preview-strip-on-a-stack). |
| `hotkey` | Global hotkey that switches to this profile. |
| `stack_hotkeys` | Per-slot hotkeys that cycle the stack in that slot: `{"center:1": Meta+Ctrl+Q}`. |

### Slot names

Slots are written `monitor:slot`, e.g. `center:0`. Slots are numbered **row by row**, `0` = top left
(a 2×2 grid is `0 1 / 2 3`). Cells of a [subgrid](#subgrids) are written `monitor:slot.sub`, e.g. `center:1.3`.

### assign

```yaml
assign:
  "Main": center:0                                       # short form
  "Alt 1": {monitor: left, slot: 0, span: [1, 2]}        # long form: span 1 column x 2 rows
  "Alt 2": center:1                                      # several characters on one slot = stack
  "Alt 3": center:1                                      #   (first entry is on top)
  "Scout Alt": center:1.3                                # subgrid cell
```

Assigned characters that aren't open keep their slot free. Characters that aren't logged in can be planned
in the web UI via "Add character".

### fill and stacking

All clients without an assignment fill the free slots of the monitors listed under `fill`, alphabetically.
Once all fill slots are taken, further clients are **stacked** onto those slots in turn
(disable with `stack_overflow: false`), unless [overflow slots](#overflow) are defined.

### disabled_monitors

```yaml
disabled_monitors: [left, right]
```

The monitor gets no slots, is skipped when filling and shown hatched in the web UI preview. Assignments to it
are kept and are filled onto the remaining monitors in the meantime.

### Grids and weights

A grid is `"COLSxROWS"` or a mapping:

```yaml
grids:
  center: {cols: 2, rows: 2, col_weights: [2, 1]}     # left column twice as wide
  right:
    cols: 2
    rows: 2
    row_weights: [1, 1]
    row_col_weights: {1: [75, 25]}                     # row 1 has its own column split
```

- `col_weights` / `row_weights`: relative sizes of columns / rows.
- `row_col_weights`: per-row column weights – vertical grid lines can differ per row.
- In the web UI these are set by dragging the grid lines (see [Web UI](web-ui.md#grid-lines)).

### Subgrids

Split a cell into its own grid to fit smaller clients:

```yaml
subgrids:
  "center:1": "2x2"
assign:
  "Scout Alt": "center:1.3"
```

Sub-cells (`center:1.0`, `center:1.1` …) work like normal slots: assign, stack, keep free, auto-fill.
A subgrid accepts the same mapping form (with weights) as a grid.

### overflow

```yaml
overflow: [{cell: "right:2", max: 3}, "right:3"]
```

Overflow slots are not filled normally. Once all fill slots are taken, further clients go there in order
(as a stack). `max` limits the number of characters; the **last** overflow slot always takes all remaining
clients and therefore has no maximum. Without overflow slots, extra clients are stacked in turn.

### blocked

Kept-free slots never receive EVE clients, not even when filling or stacking. They can stay empty, hold
another program, a stack of programs, catch new windows, or show [live previews](previews.md).

```yaml
blocked:
  "left:3": Browser                                  # just keep free (label only)
  "right:3": {label: RIFT, match: "RIFT"}            # move the first matching window here
  "right:2": {label: Code, match: "code", stack: true}
  "left:2": {label: New windows, catch_all: true, resize: false, exclude: "firefox|dolphin"}
  "center:1": {label: Alts, preview: hidden, show: eve}
```

| Key | Description |
|---|---|
| `label` | Name shown in the web UI. |
| `match` | Case-insensitive regex matched against the window **title or window class** of non-EVE windows. |
| `stack` | `true`: **all** matching windows go onto the slot as a stack (first match on top). Default: only the first match. |
| `catch_all` | `true`: every newly opened window that no other slot matches is moved here (requires auto placement). |
| `exclude` | Regex (title or class) of windows the catch-all ignores. |
| `resize` | `false`: keep the window's own size (capped to the slot, centered). Default `true`. |
| `preview` | `all` or `hidden` – turns the slot into a [preview slot](previews.md#preview-slots). |
| `show` | For preview slots: `always` (default) or `eve` (only while an EVE client is active). |

`match`, `stack`, `catch_all`, `exclude` and `resize` are explained in detail in
[Window zones](window-zones.md).

### stack_previews

```yaml
stack_previews:
  "center:0": {mode: stack, edge: right, size: 20, show: always}
```

See [Previews](previews.md#preview-strip-on-a-stack).

## hotkeys

```yaml
hotkeys:
  next_profile: Meta+Ctrl+PgDown
  prev_profile: Meta+Ctrl+PgUp
  cycle_stack: Meta+Ctrl+Tab
```

Qt key notation (e.g. `Meta+Ctrl+Right`). Profile hotkeys and stack hotkeys are set per profile (`hotkey`,
`stack_hotkeys`). See [Hotkeys](hotkeys-appearance.md#hotkeys).

## Grid calculation

1. **Monitor area:** logical coordinates (rotation and scaling already applied).
2. **Panel deduction** (`reserve`): `auto` uses the KWin work area (`MaximizeArea`, i.e. without
   taskbars), or manually `{top, right, bottom, left}`.
3. **Padding** per monitor, then the **grid** `cols x rows` with optional weights and `gap`
   (the gap is at least the separator width). Edges are rounded cumulatively so no pixels are lost.
4. **Decoration:** KWin sets the frame geometry (including the title bar), so nothing is deducted.
   The X11 backend sets the client geometry, so `settings.decoration` is deducted there.

`span: [columns, rows]` merges cells.

## Saving from the web UI

Before saving, the file is validated; the previous version is kept as `config.yaml.bak`. With
**ruamel.yaml** installed, comments and formatting outside the edited profile are preserved. Without
ruamel.yaml, PyYAML rewrites the file and comments are lost.
