"""Grid scanning utilities for stash/hero inventory detection."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import pyautogui
from PIL import Image


@dataclass(frozen=True)
class ROI:
    x: int
    y: int
    w: int
    h: int

    @classmethod
    def from_dict(cls, data: dict[str, int]) -> "ROI":
        return cls(x=data["x"], y=data["y"], w=data["w"], h=data["h"])


@dataclass(frozen=True)
class GridSpec:
    rows: int
    cols: int


@dataclass(frozen=True)
class Cell:
    row: int
    col: int
    center_x: int
    center_y: int
    is_empty: bool
    match_score: float


def _resolve_template(base_dir: Path, key: str, data: dict[str, Any]) -> Path:
    template = Path(data[key])
    if not template.is_absolute():
        template = base_dir / template
    return template


@dataclass
class BotConfig:
    stash_roi: ROI
    hero_bag_roi: ROI
    tab1: tuple[int, int]
    tab2: tuple[int, int]
    stash_grid: GridSpec
    hero_bag_grid: GridSpec
    stash_empty_slot_template: Path
    hero_bag_empty_slot_template: Path
    match_threshold: float
    action_delay_sec: float
    scan_delay_sec: float

    @classmethod
    def load(cls, config_path: str | Path) -> "BotConfig":
        path = Path(config_path)
        with path.open(encoding="utf-8") as f:
            data = json.load(f)

        base_dir = path.parent

        hero_roi_data = data.get("hero_bag_roi", data.get("hero_roi"))
        hero_grid_data = data.get("hero_bag_grid", data.get("hero_grid"))
        hero_template_key = (
            "hero_bag_empty_slot_template"
            if "hero_bag_empty_slot_template" in data
            else "hero_empty_slot_template"
        )
        if hero_template_key not in data:
            hero_template_key = "empty_slot_template"

        return cls(
            stash_roi=ROI.from_dict(data["stash_roi"]),
            hero_bag_roi=ROI.from_dict(hero_roi_data),
            tab1=(data["tab1"]["x"], data["tab1"]["y"]),
            tab2=(data["tab2"]["x"], data["tab2"]["y"]),
            stash_grid=GridSpec(**data["stash_grid"]),
            hero_bag_grid=GridSpec(**hero_grid_data),
            stash_empty_slot_template=_resolve_template(
                base_dir, "empty_slot_template", data
            ),
            hero_bag_empty_slot_template=_resolve_template(
                base_dir, hero_template_key, data
            ),
            match_threshold=float(data.get("match_threshold", 0.85)),
            action_delay_sec=float(data.get("action_delay_sec", 0.25)),
            scan_delay_sec=float(data.get("scan_delay_sec", 0.1)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "stash_roi": {
                "x": self.stash_roi.x,
                "y": self.stash_roi.y,
                "w": self.stash_roi.w,
                "h": self.stash_roi.h,
            },
            "hero_bag_roi": {
                "x": self.hero_bag_roi.x,
                "y": self.hero_bag_roi.y,
                "w": self.hero_bag_roi.w,
                "h": self.hero_bag_roi.h,
            },
            "tab1": {"x": self.tab1[0], "y": self.tab1[1]},
            "tab2": {"x": self.tab2[0], "y": self.tab2[1]},
            "stash_grid": {"rows": self.stash_grid.rows, "cols": self.stash_grid.cols},
            "hero_bag_grid": {
                "rows": self.hero_bag_grid.rows,
                "cols": self.hero_bag_grid.cols,
            },
            "empty_slot_template": "templates/stash_empty_slot.png",
            "hero_bag_empty_slot_template": "templates/hero_bag_empty_slot.png",
            "match_threshold": self.match_threshold,
            "action_delay_sec": self.action_delay_sec,
            "scan_delay_sec": self.scan_delay_sec,
        }

    def save(self, config_path: str | Path) -> None:
        path = Path(config_path)
        with path.open("w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
            f.write("\n")


def _pil_to_bgr(image: Image.Image) -> np.ndarray:
    rgb = np.array(image.convert("RGB"))
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def load_template_bgr(template_path: Path) -> np.ndarray:
    image = Image.open(template_path)
    return _pil_to_bgr(image)


def capture_roi(roi: ROI) -> np.ndarray:
    screenshot = pyautogui.screenshot(region=(roi.x, roi.y, roi.w, roi.h))
    return _pil_to_bgr(screenshot)


def cell_bounds(roi: ROI, grid: GridSpec, row: int, col: int) -> tuple[int, int, int, int]:
    cell_w = roi.w / grid.cols
    cell_h = roi.h / grid.rows
    x0 = int(col * cell_w)
    y0 = int(row * cell_h)
    x1 = int((col + 1) * cell_w) if col < grid.cols - 1 else roi.w
    y1 = int((row + 1) * cell_h) if row < grid.rows - 1 else roi.h
    return x0, y0, x1, y1


def cell_center(roi: ROI, grid: GridSpec, row: int, col: int) -> tuple[int, int]:
    x0, y0, x1, y1 = cell_bounds(roi, grid, row, col)
    return roi.x + (x0 + x1) // 2, roi.y + (y0 + y1) // 2


def match_score(cell_bgr: np.ndarray, template_bgr: np.ndarray) -> float:
    if cell_bgr.size == 0 or template_bgr.size == 0:
        return 0.0

    cell_h, cell_w = cell_bgr.shape[:2]
    template_resized = cv2.resize(template_bgr, (cell_w, cell_h), interpolation=cv2.INTER_AREA)

    diff = cv2.absdiff(cell_bgr, template_resized)
    pixel_score = 1.0 - (float(diff.mean()) / 255.0)

    result = cv2.matchTemplate(cell_bgr, template_resized, cv2.TM_CCOEFF_NORMED)
    template_score = float(result[0][0])
    if not np.isfinite(template_score) or template_score <= 0.01:
        return pixel_score

    return template_score


def scan_grid(
    roi: ROI,
    grid: GridSpec,
    template_bgr: np.ndarray,
    threshold: float,
    roi_image: np.ndarray | None = None,
) -> list[Cell]:
    image = roi_image if roi_image is not None else capture_roi(roi)
    cells: list[Cell] = []

    for row in range(grid.rows):
        for col in range(grid.cols):
            x0, y0, x1, y1 = cell_bounds(roi, grid, row, col)
            cell_img = image[y0:y1, x0:x1]
            score = match_score(cell_img, template_bgr)
            center_x, center_y = cell_center(roi, grid, row, col)
            cells.append(
                Cell(
                    row=row,
                    col=col,
                    center_x=center_x,
                    center_y=center_y,
                    is_empty=score >= threshold,
                    match_score=score,
                )
            )

    return cells


def count_empty_cells(
    roi: ROI,
    grid: GridSpec,
    template_bgr: np.ndarray,
    threshold: float,
    roi_image: np.ndarray | None = None,
) -> int:
    cells = scan_grid(roi, grid, template_bgr, threshold, roi_image)
    return sum(1 for cell in cells if cell.is_empty)


def find_item_cells(
    roi: ROI,
    grid: GridSpec,
    template_bgr: np.ndarray,
    threshold: float,
    roi_image: np.ndarray | None = None,
) -> list[Cell]:
    cells = scan_grid(roi, grid, template_bgr, threshold, roi_image)
    return [cell for cell in cells if not cell.is_empty]


def find_bag_item_cells(
    hero_bag_roi: ROI,
    hero_bag_grid: GridSpec,
    hero_bag_empty_template_bgr: np.ndarray,
    threshold: float,
    roi_image: np.ndarray | None = None,
) -> list[Cell]:
    """Find items only inside the Hero bag grid (not equipment slots).

    Requires hero_bag_roi to exclude the equipment area above the bag.
    Uses a Hero-bag-specific empty-slot template so equipped gear is never scanned.
    """
    return find_item_cells(
        hero_bag_roi,
        hero_bag_grid,
        hero_bag_empty_template_bgr,
        threshold,
        roi_image,
    )
