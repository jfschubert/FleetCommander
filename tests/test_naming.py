import unittest

from fcwm.geometry import Rect
from fcwm.monitors import Monitor
from fcwm.naming import arrangement


def mon(name, x, y, w=1920, h=1080, primary=False):
    return Monitor(name, Rect(x, y, w, h), primary=primary)


class NamingTest(unittest.TestCase):
    def slugs(self, mons):
        return {k: v["slug"] for k, v in arrangement(mons).items()}

    def test_single_row_counts_from_primary(self):
        mons = [mon("L2", 0, 0), mon("L1", 1920, 0), mon("P", 3840, 0, primary=True), mon("R", 5760, 0)]
        self.assertEqual(self.slugs(mons), {"L2": "left-2", "L1": "left-1", "P": "primary", "R": "right"})

    def test_two_by_three_with_primary_bottom_center(self):
        mons = [mon("A", 0, 0), mon("B", 1920, 0), mon("C", 3840, 0),
                mon("D", 0, 1080), mon("E", 1920, 1080, primary=True), mon("F", 3840, 1080)]
        got = arrangement(mons)
        self.assertEqual({k: v["slug"] for k, v in got.items()},
                         {"A": "top-left", "B": "top-center", "C": "top-right",
                          "D": "bottom-left", "E": "bottom-center", "F": "bottom-right"})
        self.assertTrue(got["E"]["primary"])

    def test_mixed_portrait_and_landscape_is_one_row(self):
        # as with portrait left/right and landscape in the center (center set lower)
        mons = [mon("DP-5", 0, 0, 2160, 3840), mon("DP-1", 2160, 1354, 3840, 2160, primary=True),
                mon("DP-4", 6000, 0, 2160, 3840)]
        self.assertEqual(self.slugs(mons), {"DP-5": "left", "DP-1": "primary", "DP-4": "right"})

    def test_without_primary_falls_back_to_leftmost(self):
        self.assertEqual(self.slugs([mon("A", 0, 0), mon("B", 1920, 0)]), {"A": "primary", "B": "right"})


if __name__ == "__main__":
    unittest.main()
