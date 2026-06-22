"""Unit tests for point-based slot detection logic."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from grid_utils import HeroRow1, Point, Size, hero_row1_centers, is_slot_empty, match_score


class GridUtilsTest(unittest.TestCase):
    def test_hero_row1_centers_interpolates(self) -> None:
        hero_row1 = HeroRow1(
            first_cell=Point(x=0, y=100),
            last_cell=Point(x=70, y=100),
            cols=8,
        )
        centers = hero_row1_centers(hero_row1)
        self.assertEqual(len(centers), 8)
        self.assertEqual(centers[0], (0, 100))
        self.assertEqual(centers[7], (70, 100))
        self.assertEqual(centers[4], (40, 100))

    def test_hero_row1_centers_single_col(self) -> None:
        hero_row1 = HeroRow1(
            first_cell=Point(x=10, y=20),
            last_cell=Point(x=999, y=888),
            cols=1,
        )
        self.assertEqual(hero_row1_centers(hero_row1), [(10, 20)])

    def test_match_score_identical(self) -> None:
        cell = np.full((20, 20, 3), 40, dtype=np.uint8)
        template = np.full((20, 20, 3), 40, dtype=np.uint8)
        self.assertAlmostEqual(match_score(cell, template), 1.0, places=2)

    def test_is_slot_empty_with_provided_image(self) -> None:
        template = np.full((10, 10, 3), 40, dtype=np.uint8)
        empty_image = np.full((10, 10, 3), 40, dtype=np.uint8)
        full_image = np.full((10, 10, 3), 200, dtype=np.uint8)
        crop_size = Size(w=10, h=10)

        self.assertTrue(
            is_slot_empty(0, 0, template, crop_size, 0.85, slot_image=empty_image)
        )
        self.assertFalse(
            is_slot_empty(0, 0, template, crop_size, 0.85, slot_image=full_image)
        )


if __name__ == "__main__":
    unittest.main()
