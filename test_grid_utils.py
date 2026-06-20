"""Unit tests for grid detection logic (no screen capture required)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from grid_utils import (
    GridSpec,
    ROI,
    count_empty_cells,
    find_bag_item_cells,
    find_item_cells,
    match_score,
    scan_grid,
)


class GridUtilsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.roi = ROI(x=0, y=0, w=80, h=40)
        self.grid = GridSpec(rows=2, cols=4)
        self.template = np.full((20, 20, 3), 40, dtype=np.uint8)
        self.roi_image = np.full((40, 80, 3), 40, dtype=np.uint8)
        self.roi_image[0:20, 40:60] = (200, 50, 50)

    def test_match_score_identical(self) -> None:
        cell = np.full((20, 20, 3), 40, dtype=np.uint8)
        score = match_score(cell, self.template)
        self.assertAlmostEqual(score, 1.0, places=2)

    def test_match_score_different(self) -> None:
        cell = np.full((20, 20, 3), 200, dtype=np.uint8)
        score = match_score(cell, self.template)
        self.assertLess(score, 0.5)

    def test_scan_grid_finds_one_item(self) -> None:
        cells = scan_grid(self.roi, self.grid, self.template, 0.85, self.roi_image)
        empty_count = sum(1 for c in cells if c.is_empty)
        item_count = sum(1 for c in cells if not c.is_empty)
        self.assertEqual(empty_count, 7)
        self.assertEqual(item_count, 1)

    def test_count_and_find_helpers(self) -> None:
        self.assertEqual(
            count_empty_cells(
                self.roi, self.grid, self.template, 0.85, self.roi_image
            ),
            7,
        )
        items = find_item_cells(
            self.roi, self.grid, self.template, 0.85, self.roi_image
        )
        self.assertEqual(len(items), 1)
        self.assertEqual((items[0].row, items[0].col), (0, 2))

    def test_find_bag_item_cells_uses_hero_bag_roi_only(self) -> None:
        bag_roi = ROI(x=0, y=0, w=80, h=20)
        bag_grid = GridSpec(rows=1, cols=4)
        bag_template = np.full((20, 20, 3), 40, dtype=np.uint8)

        bag_image = np.full((20, 80, 3), 40, dtype=np.uint8)
        bag_image[0:20, 40:60] = (200, 50, 50)

        items = find_bag_item_cells(
            bag_roi, bag_grid, bag_template, 0.85, bag_image
        )
        self.assertEqual(len(items), 1)
        self.assertEqual((items[0].row, items[0].col), (0, 2))


if __name__ == "__main__":
    unittest.main()
