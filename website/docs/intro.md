---
slug: /
sidebar_position: 1
title: Introduction
description: FleetCommander (fcwm) arranges EVE Online client windows on KDE Plasma in per-monitor grids.
---

# FleetCommander

**FleetCommander** (`fcwm`) arranges EVE Online clients on KDE Plasma (Wayland **and** X11) using a
grid per monitor. Profiles define which character goes into which slot. You control it from the CLI,
a KDE shortcut or the built-in web UI.

## Features

- **Per-monitor grids** with movable grid lines, column/row spans and nested **subgrids** for smaller clients.
- **Profiles**: assign characters to slots, fill free slots automatically, switch layouts with a hotkey.
- **Stacks**: several clients share one spot; a hotkey cycles through them.
- **Auto placement**: a listener places clients as soon as they log in – several simultaneous logins are batched.
- **Window zones**: keep slots free for other programs (browser, RIFT, editor …), stack matching windows there
  or catch every newly opened window in one slot.
- **Live previews** *(experimental)* like EVE-O Preview, rendered by KWin itself (no screen capture).
- **Lock**, hidden **title bars** and **separator lines** between clients.
- **Web UI** with a drag & drop profile editor, available in English and German.

fcwm only arranges, switches and previews windows – it **never sends input to clients** (same category as
EVE-O Preview). Tested with Plasma 6.7 / KWin 6.7 (Wayland).

## Not just for EVE

[Window zones](window-zones.md) work with any window, so fcwm is also a general grid tiler for KDE Plasma.
I use it at work to arrange my development environment: IDE, terminals, browser and chat each get a fixed
spot, and a hotkey switches between layouts.

## Where to go next

- [Installation](installation.md) – dependencies and the Arch package.
- [Quick start & CLI](quick-start.md) – the first commands and the full command reference.
- [Web UI](web-ui.md) – the profile editor.
- [Configuration reference](configuration.md) – every key in `config.yaml`.
