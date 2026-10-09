---
sidebar_position: 23
title: Übersetzungen
---

# Übersetzungen

fcwm gibt es auf Englisch und Deutsch. Eine weitere Sprache braucht keine Codeänderung – nur JSON-Dateien.

## Wo die Texte liegen {#where-the-strings-live}

Alle Texte der Web-UI und der CLI liegen in flachen JSON-Dateien, eine pro Sprache:

| Dateien | Inhalt |
|---|---|
| `fcwm/locales/web/<lang>.json` | Web-UI |
| `fcwm/locales/server/<lang>.json` | CLI- und Server-Meldungen, Fehler |

- **Englisch (`en.json`) ist die Ausgangssprache.** Fehlende Schlüssel fallen auf Englisch zurück.
- Platzhalter sehen aus wie `{name}` und **müssen** in der Übersetzung unverändert erhalten bleiben.

## Eine Sprache hinzufügen {#adding-a-language}

1. In beiden Ordnern `en.json` unter dem neuen Sprachcode kopieren, z. B. `fr.json` oder `pt_BR.json`, und die
   Werte übersetzen.
2. In `locales/web/<lang>.json` bei `languageName` den eigenen Namen der Sprache eintragen (z. B.
   `"Français"`) – so erscheint sie im Sprachmenü der Web-UI.

Danach:

- Das Sprachmenü der Web-UI listet automatisch jede Datei in `locales/web/`.
- Die CLI akzeptiert den neuen Code über `--lang` oder `settings.language`.
- Web-Texte werden bei jeder Anfrage gelesen, eine neu geholte Übersetzung erscheint also nach dem Neuladen der
  Seite. Server-Texte brauchen `fcwm restart`.

## Übersetzen mit Weblate {#translating-with-weblate}

Ein Weblate-Projekt mit **zwei Komponenten** anlegen, beide mit dem Dateiformat **„JSON file“** (einsprachig):

| Komponente | Dateimaske | Einsprachige Basisdatei | Vorlage für neue Übersetzungen |
|---|---|---|---|
| Web UI | `fcwm/locales/web/*.json` | `fcwm/locales/web/en.json` | `fcwm/locales/web/en.json` |
| CLI & server | `fcwm/locales/server/*.json` | `fcwm/locales/server/en.json` | `fcwm/locales/server/en.json` |

- Ausgangssprache: **Englisch**.
- Optionale Add-ons: **Cleanup translation files** und **Add missing languages**.
- Weblate schreibt Commits zurück ins Repository oder öffnet Merge-/Pull-Requests – je nach Projekteinstellung.

## Diese Dokumentation {#this-documentation}

Die Doku-Seite wird mit Docusaurus i18n übersetzt: Die Markdown-Seiten einer Sprache liegen in
`website/i18n/<lang>/docusaurus-plugin-content-docs/current/`, die Texte für Navigationsleiste, Fusszeile und
Seitenleiste in den JSON-Dateien daneben (`npm run write-translations -- --locale <lang>` legt sie an). Eine neue
Doku-Sprache braucht ausserdem einen Eintrag in `i18n.locales` in `website/docusaurus.config.js`.

Weblate kann diese Seiten bei Bedarf als Komponente vom Typ **„Markdown file“** verwalten; derzeit werden sie von
Hand gepflegt.
