"""Unit tests for color-based slot detection logic."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

from grid_utils import BotConfig, Point, RGBColor, color_distance, is_same_empty_color, is_stash_full


class ColorUtilsTest(unittest.TestCase):
    def test_color_distance_identical(self) -> None:
        color = RGBColor(r=40, g=42, b=38)
        self.assertAlmostEqual(color_distance(color, color), 0.0)

    def test_color_distance_different(self) -> None:
        empty = RGBColor(r=40, g=42, b=38)
        item = RGBColor(r=120, g=80, b=60)
        self.assertGreater(color_distance(empty, item), 15)

    def test_is_same_empty_color_within_tolerance(self) -> None:
        reference = RGBColor(r=40, g=42, b=38)
        close = RGBColor(r=42, g=44, b=40)
        self.assertTrue(is_same_empty_color(close, reference, 15))

    def test_is_same_empty_color_outside_tolerance(self) -> None:
        reference = RGBColor(r=40, g=42, b=38)
        item = RGBColor(r=120, g=80, b=60)
        self.assertFalse(is_same_empty_color(item, reference, 15))

    def test_is_stash_full_when_color_differs(self) -> None:
        config = BotConfig(
            hero_slots=[Point(x=0, y=0)] * 7,
            stash_last_slot=Point(x=100, y=100),
            stash_tabs=[Point(x=0, y=0), Point(x=1, y=1), Point(x=2, y=2)],
            empty_slot_color=RGBColor(r=40, g=42, b=38),
            color_tolerance=15,
            sample_size=5,
            action_delay_sec=0.25,
            scan_delay_sec=0.1,
            stash_tab_switch_delay_sec=0.6,
        )

        with patch("grid_utils.stash_last_slot_color", return_value=RGBColor(r=120, g=80, b=60)):
            self.assertTrue(is_stash_full(config))

        with patch("grid_utils.stash_last_slot_color", return_value=RGBColor(r=41, g=43, b=39)):
            self.assertFalse(is_stash_full(config))


if __name__ == "__main__":
    unittest.main()
