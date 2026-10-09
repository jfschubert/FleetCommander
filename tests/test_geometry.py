import re
import unittest
from pathlib import Path

from fcwm.backends.base import Window
from fcwm.config import parse_text
from fcwm.geometry import GridSpec, Insets, Rect, grid_cells, span_cells
from fcwm.layout import make_plan
from fcwm.monitors import Monitor

ROOT = Path(__file__).resolve().parent.parent


class GridTest(unittest.TestCase):
    def test_2x2_no_pixel_loss(self):
        cells = grid_cells(Rect(0, 0, 1921, 1081), GridSpec(2, 2))
        self.assertEqual(cells[0], Rect(0, 0, 960, 540))
        self.assertEqual(cells[3].x + cells[3].w, 1921)
        self.assertEqual(cells[3].y + cells[3].h, 1081)

    def test_gap_and_weights(self):
        cells = grid_cells(Rect(100, 0, 1010, 100), GridSpec(2, 1, (2, 1)), gap=10)
        self.assertEqual(cells, [Rect(100, 0, 667, 100), Rect(777, 0, 333, 100)])

    def test_span(self):
        g = GridSpec(2, 2)
        cells = grid_cells(Rect(0, 0, 200, 200), g)
        self.assertEqual(span_cells(cells, g, 0, (1, 2)), Rect(0, 0, 100, 200))
        with self.assertRaises(ValueError):
            span_cells(cells, g, 1, (2, 1))

    def test_columns_per_row(self):
        # row 0 = 50:50, row 1 = 75:25
        g = GridSpec.parse({"cols": 2, "rows": 2, "row_col_weights": {1: [75, 25]}})
        cells = grid_cells(Rect(0, 0, 400, 200), g)
        self.assertEqual([c.w for c in cells], [200, 200, 300, 100])
        self.assertEqual(cells[3].x, 300)
        self.assertFalse(g.uniform)
        self.assertTrue(GridSpec.parse({"cols": 2, "rows": 2, "row_col_weights": {1: [1, 1]}}).uniform)

    def test_insets(self):
        self.assertEqual(Insets.parse({"bottom": 44}).apply(Rect(0, 0, 100, 100)), Rect(0, 0, 100, 56))


class PlanTest(unittest.TestCase):
    def setUp(self):
        p = ROOT / "tests" / "fixtures" / "config.yaml"
        self.cfg = parse_text(p.read_text(), p)
        self.mons = [Monitor("DP-5", Rect(0, 0, 2160, 3840)),
                     Monitor("DP-1", Rect(2160, 1354, 3840, 2160), workarea=Rect(2160, 1354, 3840, 2116)),
                     Monitor("DP-4", Rect(6000, 0, 2160, 3840))]

    def win(self, i, title, cls="steam_app_8500"):
        return Window(str(i), title, cls, i, Rect(0, 0, 10, 10))

    def test_assign_fill_and_filter(self):
        wins = [self.win(1, "EVE - Xondana Fulier"), self.win(2, "EVE - New Alt"),
                self.win(3, "EVE Launcher"), self.win(4, "EVE - Foo - Brave", "brave-browser")]
        plan = make_plan(self.cfg, "Solo-Mining", wins, self.mons)
        got = {p.label for p in plan.placements}
        # New Alt lands in the first free fill slot (left:0/1 are reserved for missing chars)
        self.assertEqual(got, {"Xondana Fulier@center:0", "New Alt@left:2"})
        self.assertEqual(plan.placements[0].rect, Rect(2160, 1354, 3840, 2116))  # panel deducted
        self.assertIn("Lady Forever", plan.missing)

    def test_decoration_for_client_geometry_backends(self):
        self.cfg.decoration = Insets(30, 2, 2, 2)
        plan = make_plan(self.cfg, "Solo-Mining", [self.win(1, "EVE - Xondana Fulier")], self.mons,
                         frame_geometry=False)
        self.assertEqual(plan.placements[0].rect, Rect(2162, 1384, 3836, 2084))



class StackTest(PlanTest):
    def test_pinned_stack_and_raise_order(self):
        from fcwm.config import parse_profile
        prof = parse_profile("Stack", {"assign": {"A": "center:0", "B": "center:0", "C": "left:0"}},
                             self.cfg.monitors)
        wins = [self.win(1, "EVE - A"), self.win(2, "EVE - B"), self.win(3, "EVE - C")]
        plan = make_plan(self.cfg, prof, wins, self.mons)
        rects = {p.char: p.rect for p in plan.placements}
        self.assertEqual(rects["A"], rects["B"])
        # B to front first, then A -> A (first entry) is on top
        self.assertEqual(plan.raise_order(), ["2", "1"])
        self.assertEqual(plan.raise_order({"2"}), ["2"])

    def test_overflow_stacks_round_robin(self):
        from fcwm.config import parse_profile
        prof = parse_profile("One", {"grids": {"center": "2x1"}, "fill": ["center"], "stack_overflow": True},
                             self.cfg.monitors)
        wins = [self.win(i, f"EVE - Alt{i}") for i in range(1, 6)]
        plan = make_plan(self.cfg, prof, wins, self.mons)
        got = {p.char: f"{p.monitor}:{p.slot}" for p in plan.placements}
        self.assertEqual(got, {"Alt1": "center:0", "Alt2": "center:1", "Alt3": "center:0",
                               "Alt4": "center:1", "Alt5": "center:0"})
        self.assertEqual(plan.unplaced, [])


class DisabledMonitorTest(PlanTest):
    def test_disabled_monitor_gets_no_slots(self):
        from fcwm.config import parse_profile
        prof = parse_profile("D", {"assign": {"A": "left:0"}, "fill": ["left", "right"],
                                   "disabled_monitors": ["left"]}, self.cfg.monitors)
        plan = make_plan(self.cfg, prof, [self.win(1, "EVE - A"), self.win(2, "EVE - B")], self.mons)
        self.assertNotIn("left", plan.layouts)
        self.assertEqual(plan.disabled, ["left"])
        got = {p.char: f"{p.monitor}:{p.slot}" for p in plan.placements}
        self.assertEqual(got, {"A": "right:0", "B": "right:1"})   # A lands on right via fill
        self.assertTrue(any("left" in w for w in plan.warnings))

    def test_overflow_stacks_by_default(self):
        from fcwm.config import parse_profile
        prof = parse_profile("O", {"grids": {"center": "1x1"}, "fill": ["center"]}, self.cfg.monitors)
        plan = make_plan(self.cfg, prof, [self.win(i, f"EVE - X{i}") for i in range(3)], self.mons)
        self.assertEqual({p.slot for p in plan.placements}, {0})
        self.assertEqual(len(plan.placements), 3)


class BlockedCellTest(PlanTest):
    def test_blocked_cell_is_skipped_and_hosts_other_window(self):
        from fcwm.config import parse_profile
        prof = parse_profile("B", {"grids": {"center": "2x1"}, "fill": ["center"],
                                   "blocked": {"center:1": {"label": "RIFT", "match": "^rift"}}},
                             self.cfg.monitors)
        wins = [self.win(1, "EVE - A"), self.win(2, "EVE - B"), self.win(3, "RIFT Intel", "java")]
        plan = make_plan(self.cfg, prof, wins, self.mons)
        self.assertEqual({p.slot for p in plan.placements}, {0})      # both stacked on slot 0
        self.assertEqual([(p.window.id, p.slot) for p in plan.extra], [("3", 1)])
        self.assertEqual(plan.blocked[0]["window"], "RIFT Intel")

    def test_preview_cell(self):
        from fcwm.config import model_to_raw, parse_profile, profile_to_model
        prof = parse_profile("P", {"grids": {"center": "2x1"}, "fill": ["center"],
                                   "blocked": {"center:1": {"label": "Alts", "preview": "hidden", "match": "x"}}},
                             self.cfg.monitors)
        plan = make_plan(self.cfg, prof, [self.win(1, "EVE - A"), self.win(2, "EVE - B")], self.mons)
        self.assertEqual({p.slot for p in plan.placements}, {0})          # preview cell stays free
        self.assertEqual(plan.blocked[0]["preview"], "hidden")
        self.assertEqual(plan.blocked[0]["match"], "")                    # preview excludes window pattern
        raw = model_to_raw(self.cfg, profile_to_model(self.cfg, prof))
        self.assertEqual(raw["blocked"], {"center:1": {"label": "Alts", "preview": "hidden"}})

    def test_stack_preview_strip(self):
        from fcwm.config import model_to_raw, parse_profile, profile_to_model
        prof = parse_profile("SP", {"grids": {"center": "1x1"},
                                    "stack_previews": {"center:0": {"mode": "stack", "edge": "right", "size": 20}}},
                             self.cfg.monitors)
        plan = make_plan(self.cfg, prof, [], self.mons)
        sp = plan.stack_previews[0]
        self.assertEqual(sp["stack"], [2160, 1354, 3840, 2116])
        self.assertEqual(sp["rect"], [2160 + 3840 - 768, 1354, 768, 2116])   # 20 % on the right
        raw = model_to_raw(self.cfg, profile_to_model(self.cfg, prof))
        self.assertEqual(raw["stack_previews"], {"center:0": {"mode": "stack", "edge": "right", "size": 20}})

    def test_blocked_roundtrip(self):
        from fcwm.config import model_to_raw, parse_profile, profile_to_model
        prof = parse_profile("B", {"blocked": {"left:2": "Browser", "right:3": {"label": "RIFT", "match": "rift"}}},
                             self.cfg.monitors)
        raw = model_to_raw(self.cfg, profile_to_model(self.cfg, prof))
        self.assertEqual(raw["blocked"], {"left:2": "Browser", "right:3": {"label": "RIFT", "match": "rift"}})



class WindowZoneTest(PlanTest):
    """Window cells: stack of other windows and catch-all cell for new windows."""

    def prof(self, blocked):
        from fcwm.config import parse_profile
        return parse_profile("W", {"grids": {"center": "2x2"}, "fill": ["center"], "blocked": blocked},
                             self.cfg.monitors)

    def other(self, i, title, cls, size=(800, 600), transient=False):
        return Window(str(i), title, cls, i, Rect(0, 0, *size), transient=transient)

    def test_match_takes_first_unless_stack(self):
        wins = [self.other(1, "a.py - Visual Studio Code", "code"), self.other(2, "b.py - Visual Studio Code", "code")]
        plan = make_plan(self.cfg, self.prof({"center:1": {"match": "code"}}), wins, self.mons)
        self.assertEqual([p.window.id for p in plan.extra], ["1"])
        plan = make_plan(self.cfg, self.prof({"center:1": {"match": "code", "stack": True}}), wins, self.mons)
        self.assertEqual([p.window.id for p in plan.extra], ["1", "2"])
        self.assertEqual(plan.extra[0].rect, plan.extra[1].rect)
        self.assertEqual(plan.blocked[0]["windows"], [w.caption for w in wins])
        # equally sized window stacks: first window is on top (raised last)
        self.assertEqual(plan.raise_order(), ["2", "1"])

    def test_dialogs_and_eve_windows_are_never_taken(self):
        wins = [self.other(1, "Save as – code", "code", transient=True), self.win(2, "EVE"),
                self.other(3, "code", "code")]
        plan = make_plan(self.cfg, self.prof({"center:1": {"match": "code|eve", "stack": True}}), wins, self.mons)
        self.assertEqual([p.window.id for p in plan.extra], ["3"])

    def test_catch_all_only_new_windows_rest_after_match(self):
        prof = self.prof({"center:1": {"match": "code"},
                          "center:3": {"catch_all": True, "resize": False, "exclude": "dolphin"}})
        wins = [self.other(1, "code", "code"), self.other(2, "Error", "kdialog", (300, 120)),
                self.other(3, "Home", "dolphin"), self.other(4, "old", "konsole")]
        plan = make_plan(self.cfg, prof, wins, self.mons)          # without catch_ids: catch nothing
        self.assertEqual([p.window.id for p in plan.extra], ["1"])
        plan = make_plan(self.cfg, prof, wins, self.mons, catch_ids={"1", "2", "3"})
        self.assertEqual(sorted((p.window.id, p.slot) for p in plan.extra), [("1", 1), ("2", 3)])
        self.assertEqual(plan.caught, ["2"])
        cell = plan.layouts["center"].rect(3)
        r = next(p.rect for p in plan.extra if p.window.id == "2")
        self.assertEqual((r.w, r.h), (300, 120))                   # resize: false -> size stays
        self.assertEqual((r.x + r.w // 2, r.y + r.h // 2), (cell.x + cell.w // 2, cell.y + cell.h // 2))

    def test_catch_all_ignores_own_app_window(self):
        prof = self.prof({"center:3": {"catch_all": True}})
        wins = [self.other(1, "FleetCommander", "fcwm"), self.other(2, "Konsole", "konsole")]
        plan = make_plan(self.cfg, prof, wins, self.mons, catch_ids={"1", "2"})
        self.assertEqual([p.window.id for p in plan.extra], ["2"])

    def test_window_zone_roundtrip(self):
        from fcwm.config import model_to_raw, profile_to_model
        blocked = {"center:1": {"label": "Code", "match": "code", "stack": True},
                   "center:3": {"label": "Neu", "catch_all": True, "resize": False, "exclude": "dolphin"}}
        prof = self.prof(blocked)
        self.assertTrue(prof.blocked[1].catch_all and not prof.blocked[1].resize)
        raw = model_to_raw(self.cfg, profile_to_model(self.cfg, prof))
        self.assertEqual(raw["blocked"], blocked)


class SubgridTest(PlanTest):
    def prof(self, **extra):
        from fcwm.config import parse_profile
        base = {"grids": {"center": "2x1"}, "subgrids": {"center:1": "2x2"}, "fill": ["center"]}
        base.update(extra)
        return parse_profile("Sub", base, self.cfg.monitors)

    def test_subgrid_cells_and_fill_order(self):
        wins = [self.win(i, f"EVE - Alt{i}") for i in range(1, 6)]
        plan = make_plan(self.cfg, self.prof(), wins, self.mons)
        got = {p.char: (p.slot, p.sub) for p in plan.placements}
        # Slot 0 normal, slot 1 split into 4 small cells -> 5 places
        self.assertEqual(got, {"Alt1": (0, None), "Alt2": (1, 0), "Alt3": (1, 1), "Alt4": (1, 2), "Alt5": (1, 3)})
        small = next(p.rect for p in plan.placements if p.char == "Alt2")
        self.assertEqual(small, Rect(2160 + 1920, 1354, 960, 1058))

    def test_pin_block_and_stack_in_subgrid(self):
        prof = self.prof(assign={"Main": "center:0", "Scout": "center:1.3", "Scout2": "center:1.3"},
                         blocked={"center:1.0": "RIFT"}, fill=["center"])
        wins = [self.win(1, "EVE - Main"), self.win(2, "EVE - Scout"), self.win(3, "EVE - Scout2"),
                self.win(4, "EVE - Alt")]
        plan = make_plan(self.cfg, prof, wins, self.mons)
        got = {p.char: (p.slot, p.sub) for p in plan.placements}
        self.assertEqual(got["Scout"], (1, 3))
        self.assertEqual(got["Scout2"], (1, 3))
        self.assertEqual(got["Alt"], (1, 1))           # 1.0 is kept free
        self.assertEqual(plan.raise_order(), ["3", "2"])

    def test_subgrid_roundtrip(self):
        from fcwm.config import model_to_raw, profile_to_model
        prof = self.prof(assign={"Scout": "center:1.3"}, blocked={"center:1.0": "RIFT"},
                         subgrids={"center:1": {"cols": 2, "rows": 2, "col_weights": [3, 1]}})
        raw = model_to_raw(self.cfg, profile_to_model(self.cfg, prof))
        self.assertEqual(raw["assign"], {"Scout": "center:1.3"})
        self.assertEqual(raw["blocked"], {"center:1.0": "RIFT"})
        self.assertEqual(raw["subgrids"], {"center:1": {"cols": 2, "rows": 2, "col_weights": [3.0, 1.0]}})


class OverflowTest(PlanTest):
    def test_overflow_cells_with_max(self):
        from fcwm.config import parse_profile
        prof = parse_profile("O", {"grids": {"center": "3x1"}, "fill": ["center"],
                                   "overflow": [{"cell": "center:1", "max": 2}, "center:2"]},
                             self.cfg.monitors)
        wins = [self.win(i, f"EVE - Alt{i}") for i in range(1, 7)]
        plan = make_plan(self.cfg, prof, wins, self.mons)
        got = {p.char: p.slot for p in plan.placements}
        # Slot 0 normal, 1 and 2 are overflow -> not used for normal filling
        self.assertEqual(got, {"Alt1": 0, "Alt2": 1, "Alt3": 1, "Alt4": 2, "Alt5": 2, "Alt6": 2})
        self.assertEqual([(o["order"], o["max"], o["count"]) for o in plan.overflow], [(1, 2, 2), (2, None, 3)])

    def test_overflow_roundtrip_drops_max_on_last(self):
        from fcwm.config import model_to_raw, parse_profile, profile_to_model
        prof = parse_profile("O", {"overflow": [{"cell": "center:0", "max": 2}, {"cell": "left:1.2", "max": 5}]},
                             self.cfg.monitors)
        raw = model_to_raw(self.cfg, profile_to_model(self.cfg, prof))
        self.assertEqual(raw["overflow"], [{"cell": "center:0", "max": 2}, "left:1.2"])


class SeparatorTest(unittest.TestCase):
    def test_lines_only_between_touching_windows(self):
        from fcwm.separators import compute_lines
        gap = 2
        a = Rect(0, 0, 99, 100)          # top left
        b = Rect(101, 0, 99, 100)        # right next to it (gap 2)
        c = Rect(0, 102, 200, 50)        # below, across the full width
        d = Rect(500, 0, 50, 50)         # far away -> no line
        lines = compute_lines([a, b, c, d, Rect(0, 0, 99, 100)], gap)   # duplicate (stack) counts once
        self.assertEqual(lines, [[0, 100, 99, 2], [99, 0, 2, 100], [101, 100, 99, 2]])
        self.assertEqual(compute_lines([a, b], 0), [])
        from fcwm.separators import line_pairs
        self.assertEqual(line_pairs([a, b], gap), [([99, 0, 2, 100], [0, 0, 99, 100], [101, 0, 99, 100])])


class StableFillTest(PlanTest):
    def test_existing_auto_client_keeps_its_slot(self):
        # "Zed" already sits on left:2; a new, alphabetically earlier client must not displace it
        zed = self.win(1, "EVE - Zed")
        zed.geometry = Rect(0, 1920, 1080, 1920)          # = left:2 in the 2x2 grid
        new = self.win(2, "EVE - Aaron")
        plan = make_plan(self.cfg, "Solo-Mining", [zed, new], self.mons, keep_ids={"1"})
        got = {p.char: f"{p.monitor}:{p.slot}" for p in plan.placements}
        # left:3 is kept free in the example profile -> Aaron jumps to the next free slot
        self.assertEqual(got, {"Zed": "left:2", "Aaron": "right:2"})


if __name__ == "__main__":
    unittest.main()
