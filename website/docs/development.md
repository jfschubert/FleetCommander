---
sidebar_position: 22
title: Architecture & development
---

# Architecture & development

## Module structure

```text
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
  i18n.py          message lookup (strings in fcwm/locales/)
  locales/         translations: web/<lang>.json, server/<lang>.json
  cli.py, web.py   front ends
  maintenance.py   fcwm init / open / reload / restart / cleanup
  static/          web UI – no build step, plain files served by web.py:
    index.html       markup + icon sprite
    css/app.css      styles
    js/*.js          classic scripts in load order: i18n, core, model, cells, settings, move,
                     profiles, render, gridlines, controls (shared global scope)
packaging/         systemd service, menu entry, distribution packages (arch/PKGBUILD …)
website/           this documentation (Docusaurus)
```

## Running from a checkout

```bash
./fcwm.sh apply -n          # or: python3 -m fcwm apply -n
```

`fcwm.sh` also works as the target of a KDE shortcut.

## Tests

```bash
python3 -m unittest discover -s tests
```

## Documentation

The docs live in `website/` (Docusaurus 3, English + German):

```bash
cd website
npm ci
npm start               # English dev server
npm run start:de        # German dev server
npm run build           # static site for both locales in website/build/
```

German translations are in `website/i18n/de/`. The site is published by
`.github/workflows/docs.yml` (GitHub Pages) or `.gitlab-ci.yml` (GitLab Pages); `DOCS_URL` and
`DOCS_BASE_URL` override the site URL and base path.

### Screenshots

The screenshots in the docs and on the front page come from `website/screenshots/take.py`. It starts an
isolated web UI with the demo config (placeholder characters only) and renders every page offscreen in
English and German (needs PyQt6-WebEngine):

```bash
python3 website/screenshots/take.py
```

## Releases

`packaging/bump-version.sh X.Y.Z "changelog line"` sets the version in every place it is recorded. Pushing
the tag `vX.Y.Z` runs `.github/workflows/release.yml`: tests, a version check, the Arch, Debian and Fedora
packages plus wheel and sdist, and a GitHub release with all files and `SHA256SUMS`. Details:
[`packaging/README.md`](https://github.com/jfschubert/FleetCommander/blob/master/packaging/README.md#releasing-a-new-version).
