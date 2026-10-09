"""Mini i18n for server and CLI messages; the texts live in locales/server/<language>.json.

The active language is held in a ContextVar: the web UI sets it per request
(X-Lang header), the CLI once from settings.language or $LANG.
"""
from __future__ import annotations

import json
import os
from contextvars import ContextVar
from pathlib import Path

LOCALES = Path(__file__).parent / "locales"
SOURCE = "en"   # source language: missing translations fall back to it


def load_catalog(component: str) -> dict[str, dict[str, str]]:
    """All languages of a component ("server" or "web"): {language: {key: text}}.

    One file per language (locales/<component>/<language>.json, flat JSON) – the format
    that translation tools like Weblate edit directly. New language = new file."""
    out = {}
    for f in sorted((LOCALES / component).glob("*.json")):
        try:
            out[f.stem] = {k: v for k, v in json.loads(f.read_text(encoding="utf-8")).items() if v}
        except (OSError, ValueError):
            continue
    return out


MESSAGES = load_catalog("server")
LANGUAGES = tuple(MESSAGES)


def match_language(code: str | None, available) -> str | None:
    """"de-CH"/"de_CH" -> "de_CH", otherwise "de"; None if nothing matches."""
    code = (code or "").replace("-", "_").split(".")[0]
    by_lower = {a.lower(): a for a in available}
    if code.lower() in by_lower:
        return by_lower[code.lower()]
    return by_lower.get(code[:2].lower())


_default = match_language(os.environ.get("LANG"), LANGUAGES) or SOURCE
current: ContextVar[str | None] = ContextVar("fcwm_lang", default=None)


def set_default(lang: str | None) -> None:
    global _default
    _default = match_language(lang, LANGUAGES) or _default


def lang() -> str:
    return current.get() or _default


def norm(lang: str | None) -> str:
    return match_language(lang, LANGUAGES) or _default


def t(key: str, **kw) -> str:
    text = MESSAGES.get(lang(), {}).get(key) or MESSAGES[SOURCE].get(key)
    if text is None:
        return key
    try:
        return text.format(**kw)
    except (KeyError, IndexError, ValueError):   # broken placeholder in a translation
        return MESSAGES[SOURCE].get(key, key).format(**kw)


class FcwmError(Exception):
    """Error with a translatable message; the translation happens on creation."""

    def __init__(self, key: str, **kw):
        self.key, self.kw = key, kw
        super().__init__(t(key, **kw))


class ConfigError(FcwmError, ValueError):
    pass
