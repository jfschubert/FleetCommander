---
sidebar_position: 14
title: Window zones
---

# Window zones (kept-free slots)

Besides EVE clients, fcwm can manage the other programs on your screens: a browser, RIFT, an editor, a chat
client … Each of these lives in a **kept-free slot** (`blocked` in the profile). A kept-free slot never
receives EVE clients, not even when filling or stacking.

Create one in the web UI with ⚙ → **Keep free / for other windows (browser, RIFT, catch-all …)** on an empty
slot; ⚙ → **Edit (name, windows, preview)** (or double-click) changes it, ⚙ → **Release for clients again**
turns it back into a normal slot. The editor's checkboxes map to the keys below: "Stack all matching windows"
(`stack`), "Catch-all slot for new windows" with "Don't catch (title/class, regex)" (`catch_all`, `exclude`)
and "Keep window size" (`resize: false`).

## Just keep free

```yaml
blocked:
  "left:3": Browser          # label only
```

The slot stays empty – useful for a window you place yourself.

## One window per slot

```yaml
blocked:
  "right:3": {label: RIFT, match: "RIFT|Brave"}
```

`match` is a **case-insensitive regex** tested against the window **title or window class** of non-EVE
windows (the web UI offers titles and classes of open windows to pick from). Windows of the EVE window class
(including the pre-login "EVE" launcher windows) and transient windows (dialogs) are never matched. When the profile is applied – and,
with [auto placement](auto-placement.md) on, when a matching window appears – the **first** matching window is
moved into the slot.

## Window stacks

```yaml
blocked:
  "right:2": {label: Code, match: "code", stack: true}
```

With `stack: true` **all** matching windows go onto that slot as a stack (first match on top) instead of only
the first one.

Window stacks can be cycled like EVE stacks:

- a stack hotkey on the slot: `stack_hotkeys: {"right:2": Meta+Ctrl+C}`,
- the global **cycle stack** hotkey, when a window of that stack is active.

## Catch-all zone

```yaml
blocked:
  "left:3": {label: New windows, catch_all: true, resize: false, exclude: "firefox|dolphin"}
```

While fcwm runs with **auto placement enabled**, every **newly opened** normal window that

- is not an EVE client (no window of the EVE window class, including pre-login "EVE" windows),
- is not matched by another slot's `match`, and
- is not a transient window (dialog)

is moved to the catch-all slot (stacked). Rules:

- **Existing windows are not touched** – only windows opened after fcwm started watching.
- **Dialogs and popups that belong to a parent window** (transient windows in KWin) are never moved, so a
  program's popups appear wherever the program puts them.
- `exclude` is an optional regex (title or class, case-insensitive) of windows the catch-all ignores.
- Only the **first** catch-all slot of a profile is used.

## Keep the window's size

```yaml
blocked:
  "left:3": {label: New windows, catch_all: true, resize: false}
  "right:3": {label: Messages, match: "telegram", resize: false}
```

`resize: false` keeps the window's own size, capped to the slot and centered in it. This is useful so small
error or message dialogs aren't blown up to the full slot. It works for catch-all and `match` slots alike.

## Options at a glance

| Key | Default | Description |
|---|---|---|
| `label` | – | Name shown in the web UI. |
| `match` | – | Regex (title or class, case-insensitive) of windows that belong here. |
| `stack` | `false` | Put all matching windows here as a stack (first match on top). |
| `catch_all` | `false` | Catch newly opened windows that no other slot matches. |
| `exclude` | – | Regex of windows the catch-all ignores. |
| `resize` | `true` | `false`: keep the window's size (capped to the slot, centered). |
| `preview` / `show` | – | Turn the slot into a [preview slot](previews.md#preview-slots) instead. |
