import re
import unittest

from fcwm import i18n

PLACEHOLDER = re.compile(r"\{(\w+)\}")


class LocaleFilesTest(unittest.TestCase):
    """Translations (e.g. from Weblate) must not lose or invent placeholders."""

    def check(self, component):
        cat = i18n.load_catalog(component)
        src = cat[i18n.SOURCE]
        for lang, msgs in cat.items():
            for key, text in msgs.items():
                with self.subTest(component=component, lang=lang, key=key):
                    self.assertIn(key, src, "key missing from the source language")
                    self.assertEqual(set(PLACEHOLDER.findall(text)), set(PLACEHOLDER.findall(src[key])))

    def test_server_and_web_placeholders(self):
        self.check("server")
        self.check("web")

    def test_language_matching_and_fallback(self):
        self.assertEqual(i18n.match_language("de-CH", ["de", "en"]), "de")
        self.assertEqual(i18n.match_language("pt-BR", ["pt_BR", "en"]), "pt_BR")
        self.assertIsNone(i18n.match_language("xx", ["de", "en"]))
        token = i18n.current.set("de")
        try:
            self.assertEqual(i18n.t("web_url", url="u"), "Web-UI: u")
            self.assertEqual(i18n.t("no_such_key"), "no_such_key")
        finally:
            i18n.current.reset(token)
