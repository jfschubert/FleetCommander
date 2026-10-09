---
sidebar_position: 23
title: Translations
---

# Translations

fcwm ships in English and German. Adding a language needs no code changes – only JSON files.

## Where the strings live

All UI and CLI strings are in flat JSON files, one per language:

| Files | Content |
|---|---|
| `fcwm/locales/web/<lang>.json` | Web UI |
| `fcwm/locales/server/<lang>.json` | CLI and server messages, errors |

- **English (`en.json`) is the source language.** Missing keys fall back to English.
- Placeholders look like `{name}` and **must be kept** unchanged in the translation.

## Adding a language

1. Copy `en.json` in both folders to the new language code, e.g. `fr.json` or `pt_BR.json`, and translate the values.
2. In `locales/web/<lang>.json`, set `languageName` to the language's own name (e.g. `"Français"`) – that is
   what appears in the web UI's language menu.

Then:

- The web UI's language menu lists every file in `locales/web/` automatically.
- The CLI accepts the new code via `--lang` or `settings.language`.
- Web strings are read on every request, so a newly pulled translation shows up on a page reload.
  Server strings need `fcwm restart`.

## Translating with Weblate

Create one Weblate project with **two components**, both with the file format **"JSON file"** (monolingual):

| Component | File mask | Monolingual base language file | Template for new translations |
|---|---|---|---|
| Web UI | `fcwm/locales/web/*.json` | `fcwm/locales/web/en.json` | `fcwm/locales/web/en.json` |
| CLI & server | `fcwm/locales/server/*.json` | `fcwm/locales/server/en.json` | `fcwm/locales/server/en.json` |

- Source language: **English**.
- Optional add-ons: **Cleanup translation files** and **Add missing languages**.
- Weblate pushes commits back to the repository, or opens merge/pull requests, depending on the project setup.

## This documentation

The docs site is translated with Docusaurus i18n: the Markdown pages of a language live in
`website/i18n/<lang>/docusaurus-plugin-content-docs/current/`, the navbar/footer/sidebar labels in the JSON files
next to it (`npm run write-translations -- --locale <lang>` creates them). A new docs language also needs an entry
in `i18n.locales` in `website/docusaurus.config.js`.

Weblate can handle these pages as a **"Markdown file"** component if wanted; currently they are maintained by hand.
