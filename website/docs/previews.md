---
sidebar_position: 13
title: Previews
---

# Live previews

fcwm can show live images of your clients, like EVE-O Preview. They are rendered by KWin itself
(`WindowThumbnail`) – no screen capture – and are only shown while `fcwm web` / `fcwm watch` runs.

## Preview slots

A kept-free slot can become a preview slot (⚙ → Keep free / for other windows, then ⚙ → Edit (name, windows, preview) → "Preview"):

- `preview: all` – all clients,
- `preview: hidden` – only hidden clients (behind others in a stack, or minimized).

The slot shows the clients as tiles with character names (in the title bar color); the active one is
highlighted and a click switches to the client.

**Visible** (`show`): `always` (default, like EVE-O Preview – then also on top of other programs) or `eve`
(only while an EVE client is active).

```yaml
blocked:
  "right:3": {label: Alts, preview: hidden, show: eve}   # preview: all|hidden, show: always|eve
```

## Preview strip on a stack

⚙ → **Preview strip on this stack** adds a strip of live images along one edge of the stack.

```yaml
stack_previews:
  "center:0": {mode: stack, edge: right, size: 20}   # mode: stack|all
```

| Key | Values | Description |
|---|---|---|
| `mode` | `stack` (default), `all` | *The other (hidden) clients of this stack* or *all clients*. `stack` disappears by itself when nothing is hidden. |
| `edge` | `bottom` (default), `top`, `left`, `right` | Edge of the stack. |
| `size` | 5–60, default 18 | Size in percent of the slot. |
| `show` | `always` (default), `eve` | As for preview slots. |
