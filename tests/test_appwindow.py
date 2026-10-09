import unittest

from fcwm.appwindow import is_internal


class AppWindowTest(unittest.TestCase):
    def test_local_ui_stays_in_window_any_port(self):
        self.assertTrue(is_internal("http://127.0.0.1:8765/"))
        self.assertTrue(is_internal("http://localhost:9001/#settings"))   # port change in the settings
        self.assertTrue(is_internal("http://[::1]:8765/"))

    def test_everything_else_goes_to_the_browser(self):
        self.assertFalse(is_internal("https://jfschubert.github.io/FleetCommander/"))
        self.assertFalse(is_internal("http://127.0.0.1.evil.example/"))
        self.assertFalse(is_internal("file:///etc/passwd"))


class StaticFilesTest(unittest.TestCase):
    def test_ui_files_and_no_escape(self):
        from fcwm.web import static_file
        self.assertEqual(static_file("/").name, "index.html")
        self.assertEqual(static_file("/js/core.js").name, "core.js")
        self.assertEqual(static_file("/css/app.css").name, "app.css")
        self.assertIsNone(static_file("/../web.py"))
        self.assertIsNone(static_file("/js/../../config.py"))
        self.assertIsNone(static_file("/missing.js"))
