import shutil
import tempfile
import unittest
from pathlib import Path

from fcwm import config as c

ROOT = Path(__file__).resolve().parent.parent


class ProfileEditTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.path = self.dir / "config.yaml"
        shutil.copy(ROOT / "tests" / "fixtures" / "config.yaml", self.path)
        self.cfg = c.load(str(self.path))

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_roundtrip_rename_keeps_order_default_and_weights(self):
        m = c.profile_to_model(self.cfg, self.cfg.profiles["Solo-Mining"])
        m["assign"][1]["span"] = [1, 2]
        c.save_profile(self.cfg, "Mining", m, "Solo-Mining")
        cfg = c.load(str(self.path))
        self.assertEqual(list(cfg.profiles)[0], "Mining")
        self.assertEqual(cfg.default_profile, "Mining")
        self.assertEqual(cfg.profiles["Mining"].assign[1].span, (1, 2))
        # unverändertes Raster mit Gewichtungen bleibt erhalten
        mb = c.profile_to_model(cfg, cfg.profiles["Multibox-Center"])
        c.save_profile(cfg, "Multibox-Center", mb, "Multibox-Center")
        cfg = c.load(str(self.path))
        self.assertEqual(cfg.profiles["Multibox-Center"].grids["center"].col_weights, (2, 1))
        self.assertTrue((self.dir / "config.yaml.bak").exists())

    def test_new_duplicate_name_and_delete(self):
        m = c.profile_to_model(self.cfg, self.cfg.profiles["Fleet-Fight"])
        with self.assertRaises(ValueError):
            c.save_profile(self.cfg, "Solo-Mining", m, None)
        c.save_profile(self.cfg, "Neu", m, None)
        cfg = c.load(str(self.path))
        self.assertIn("Neu", cfg.profiles)
        c.delete_profile(cfg, "Solo-Mining")
        cfg = c.load(str(self.path))
        self.assertNotIn("Solo-Mining", cfg.profiles)
        self.assertEqual(cfg.default_profile, "Fleet-Fight")

    def test_moved_grid_lines_roundtrip(self):
        m = c.profile_to_model(self.cfg, self.cfg.profiles["Multibox-Center"])
        self.assertEqual(m["weights"]["center"], [[2, 1], None, None])
        # Linie verschieben: 70/30
        m["weights"]["center"] = [[70, 30], None]
        c.save_profile(self.cfg, "Multibox-Center", m, "Multibox-Center")
        cfg = c.load(str(self.path))
        g = cfg.profiles["Multibox-Center"].grids["center"]
        self.assertEqual((g.cols, g.rows, g.col_weights, g.row_weights), (2, 2, (70.0, 30.0), ()))
        # gleichmässig zurückgesetzt -> wieder kompakte Schreibweise
        m["weights"] = {}
        self.assertEqual(c.model_to_raw(cfg, m)["grids"]["center"], "2x2")

    def test_columns_per_row_roundtrip(self):
        m = c.profile_to_model(self.cfg, self.cfg.profiles["Solo-Mining"])
        m["weights"]["left"] = [None, None, {"1": [75, 25]}]
        c.save_profile(self.cfg, "Solo-Mining", m, "Solo-Mining")
        cfg = c.load(str(self.path))
        g = cfg.profiles["Solo-Mining"].grids["left"]
        self.assertEqual(g.row_col_weights, ((1, (75.0, 25.0)),))
        self.assertEqual(c.profile_to_model(cfg, cfg.profiles["Solo-Mining"])["weights"]["left"],
                         [None, None, {"1": [75.0, 25.0]}])

    def test_settings_and_profile_hotkeys_roundtrip(self):
        c.save_settings(self.cfg, hotkeys={"next_profile": "Meta+Ctrl+Right", "prev_profile": ""},
                        titlebar={"hide": True, "color": "#b42828"},
                        characters={"Lady Forever": {"color": "#2a6f97"}, "X": {"color": ""}})
        cfg = c.load(str(self.path))
        self.assertEqual(cfg.hotkeys, {"next_profile": "Meta+Ctrl+Right"})
        self.assertEqual(cfg.titlebar, {"hide": True, "color": "#b42828"})
        self.assertEqual(cfg.characters, {"Lady Forever": {"color": "#2a6f97"}})
        m = c.profile_to_model(cfg, cfg.profiles["Fleet-Fight"])
        m["hotkey"] = "Meta+Ctrl+2"
        m["stack_hotkeys"] = {"left:0": "Meta+Q"}
        m["overflow"] = [{"monitor": "right", "slot": 2, "sub": None, "max": 2}]
        c.save_profile(cfg, "Fleet-Fight", m, "Fleet-Fight")
        p = c.load(str(self.path)).profiles["Fleet-Fight"]
        self.assertEqual((p.hotkey, p.stack_hotkeys), ("Meta+Ctrl+2", {"left:0": "Meta+Q"}))
        self.assertEqual([(o.monitor, o.slot, o.max) for o in p.overflow], [("right", 2, None)])  # letztes: kein Max

    def test_migrates_legacy_evewm_config(self):
        import os, subprocess, sys
        xdg = self.dir / "xdg"
        (xdg / "evewm").mkdir(parents=True)
        shutil.copy(ROOT / "tests" / "fixtures" / "config.yaml", xdg / "evewm" / "config.yaml")
        (xdg / "evewm" / "evewm-state.json").write_text('{"auto_place": true}')
        out = subprocess.run([sys.executable, "-c", "from fcwm import config; print(config.find_config())"],
                             cwd=ROOT, env={**os.environ, "XDG_CONFIG_HOME": str(xdg)},
                             capture_output=True, text=True)
        self.assertEqual(out.stdout.strip(), str(xdg / "fcwm" / "config.yaml"), out.stderr)
        self.assertEqual((xdg / "fcwm" / "fcwm-state.json").read_text(), '{"auto_place": true}')
        self.assertTrue((xdg / "evewm" / "config.yaml").exists())      # alter Ordner bleibt als Sicherung

    def test_invalid_model_is_not_written(self):
        before = self.path.read_text()
        m = c.profile_to_model(self.cfg, self.cfg.profiles["Fleet-Fight"])
        m["assign"].append({"char": "X", "monitor": "nope", "slot": 0, "span": [1, 1]})
        with self.assertRaises(ValueError):
            c.save_profile(self.cfg, "Fleet-Fight", m, "Fleet-Fight")
        self.assertEqual(self.path.read_text(), before)


if __name__ == "__main__":
    unittest.main()
