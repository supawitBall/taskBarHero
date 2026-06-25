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

    def test_stash_full_threshold_logic(self) -> None:
        template = np.full((10, 10, 3), 40, dtype=np.uint8)
        empty_image = np.full((10, 10, 3), 40, dtype=np.uint8)
        full_image = np.full((10, 10, 3), 200, dtype=np.uint8)
        threshold = 0.85

        self.assertGreaterEqual(match_score(empty_image, template), threshold)
        self.assertLess(match_score(full_image, template), threshold)

    def test_hero_row1_col_offset_and_crop(self) -> None:
        from grid_utils import crop_hero_row1_cell, hero_row1_col_offset_x

        hero_row1 = HeroRow1(
            first_cell=Point(x=100, y=200),
            last_cell=Point(x=700, y=200),
            cols=8,
        )
        crop_size = Size(w=20, h=20)
        strip = np.zeros((20, 620, 3), dtype=np.uint8)

        for col in range(8):
            offset = hero_row1_col_offset_x(hero_row1, col)
            strip[0:20, offset : offset + 20, :] = (col + 1) * 10

        for col in range(8):
            cell = crop_hero_row1_cell(strip, hero_row1, col, crop_size)
            expected = (col + 1) * 10
            self.assertTrue(np.all(cell[:, :, 0] == expected), f"col {col} crop misaligned")


if __name__ == "__main__":
    unittest.main()
