"""Point-based slot detection for hero row 1 and stash last slot."""

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
class Point:
    x: int
    y: int

    @classmethod
    def from_dict(cls, data: dict[str, int]) -> "Point":
        return cls(x=data["x"], y=data["y"])


@dataclass(frozen=True)
class Size:
    w: int
    h: int

    @classmethod
    def from_dict(cls, data: dict[str, int]) -> "Size":
        return cls(w=data["w"], h=data["h"])


@dataclass(frozen=True)
class HeroRow1:
    first_cell: Point
    last_cell: Point
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
    hero_row1: HeroRow1
    stash_last_slot: Point
    stash_tabs: list[Point]
    hero_bag_empty_slot_template: Path
    stash_last_slot_empty_template: Path
    slot_crop_size: Size
    match_threshold: float
    hero_empty_threshold: float
    stash_empty_threshold: float
    action_delay_sec: float
    scan_delay_sec: float
    stash_tab_switch_delay_sec: float

    @classmethod
    def load(cls, config_path: str | Path) -> "BotConfig":
        path = Path(config_path)
        with path.open(encoding="utf-8") as f:
            data = json.load(f)

        base_dir = path.parent
        hero_data = data["hero_row1"]

        return cls(
            hero_row1=HeroRow1(
                first_cell=Point.from_dict(hero_data["first_cell"]),
                last_cell=Point.from_dict(hero_data["last_cell"]),
                cols=int(hero_data["cols"]),
            ),
            stash_last_slot=Point.from_dict(data["stash_last_slot"]),
            stash_tabs=[Point.from_dict(tab) for tab in data["stash_tabs"]],
            hero_bag_empty_slot_template=_resolve_template(
                base_dir, "hero_bag_empty_slot_template", data
            ),
            stash_last_slot_empty_template=_resolve_template(
                base_dir, "stash_last_slot_empty_template", data
            ),
            slot_crop_size=Size.from_dict(data["slot_crop_size"]),
            match_threshold=float(data.get("match_threshold", 0.85)),
            hero_empty_threshold=float(
                data.get("hero_empty_threshold", data.get("match_threshold", 0.85))
            ),
            stash_empty_threshold=float(
                data.get("stash_empty_threshold", data.get("match_threshold", 0.85))
            ),
            action_delay_sec=float(data.get("action_delay_sec", 0.25)),
            scan_delay_sec=float(data.get("scan_delay_sec", 0.1)),
            stash_tab_switch_delay_sec=float(data.get("stash_tab_switch_delay_sec", 0.6)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "hero_row1": {
                "first_cell": {"x": self.hero_row1.first_cell.x, "y": self.hero_row1.first_cell.y},
                "last_cell": {"x": self.hero_row1.last_cell.x, "y": self.hero_row1.last_cell.y},
                "cols": self.hero_row1.cols,
            },
            "stash_last_slot": {"x": self.stash_last_slot.x, "y": self.stash_last_slot.y},
            "stash_tabs": [{"x": tab.x, "y": tab.y} for tab in self.stash_tabs],
            "hero_bag_empty_slot_template": "templates/hero_bag_empty_slot.png",
            "stash_last_slot_empty_template": "templates/stash_last_slot_empty.png",
            "slot_crop_size": {"w": self.slot_crop_size.w, "h": self.slot_crop_size.h},
            "match_threshold": self.match_threshold,
            "hero_empty_threshold": self.hero_empty_threshold,
            "stash_empty_threshold": self.stash_empty_threshold,
            "action_delay_sec": self.action_delay_sec,
            "scan_delay_sec": self.scan_delay_sec,
            "stash_tab_switch_delay_sec": self.stash_tab_switch_delay_sec,
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


def hero_row1_centers(hero_row1: HeroRow1) -> list[tuple[int, int]]:
    if hero_row1.cols <= 0:
        raise ValueError("hero_row1.cols must be > 0")
    if hero_row1.cols == 1:
        return [(hero_row1.first_cell.x, hero_row1.first_cell.y)]

    step_x = (hero_row1.last_cell.x - hero_row1.first_cell.x) / (hero_row1.cols - 1)
    step_y = (hero_row1.last_cell.y - hero_row1.first_cell.y) / (hero_row1.cols - 1)
    return [
        (
            int(round(hero_row1.first_cell.x + col * step_x)),
            int(round(hero_row1.first_cell.y + col * step_y)),
        )
        for col in range(hero_row1.cols)
    ]


def slot_crop_region(center_x: int, center_y: int, crop_w: int, crop_h: int) -> tuple[int, int, int, int]:
    left = center_x - crop_w // 2
    top = center_y - crop_h // 2
    return left, top, max(crop_w, 1), max(crop_h, 1)


def capture_slot_image(center_x: int, center_y: int, crop_w: int, crop_h: int) -> np.ndarray:
    left, top, width, height = slot_crop_region(center_x, center_y, crop_w, crop_h)
    screenshot = pyautogui.screenshot(region=(left, top, width, height))
    return _pil_to_bgr(screenshot)


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


def slot_match_score(
    center_x: int,
    center_y: int,
    template_bgr: np.ndarray,
    crop_size: Size,
    slot_image: np.ndarray | None = None,
) -> float:
    image = slot_image
    if image is None:
        image = capture_slot_image(center_x, center_y, crop_size.w, crop_size.h)
    return match_score(image, template_bgr)


def is_slot_empty(
    center_x: int,
    center_y: int,
    template_bgr: np.ndarray,
    crop_size: Size,
    threshold: float,
    slot_image: np.ndarray | None = None,
) -> bool:
    score = slot_match_score(center_x, center_y, template_bgr, crop_size, slot_image)
    return score >= threshold


def hero_row1_col_offset_x(hero_row1: HeroRow1, col: int) -> int:
    if hero_row1.cols <= 1:
        return 0
    span = hero_row1.last_cell.x - hero_row1.first_cell.x
    return int(round(col * span / (hero_row1.cols - 1)))


def capture_hero_row1_strip(config: BotConfig) -> np.ndarray:
    hero = config.hero_row1
    crop_w = config.slot_crop_size.w
    crop_h = config.slot_crop_size.h
    left = hero.first_cell.x - crop_w // 2
    top = hero.first_cell.y - crop_h // 2
    width = (hero.last_cell.x - hero.first_cell.x) + crop_w
    height = crop_h
    screenshot = pyautogui.screenshot(region=(left, top, width, height))
    return _pil_to_bgr(screenshot)


def crop_hero_row1_cell(
    strip: np.ndarray,
    hero_row1: HeroRow1,
    col: int,
    crop_size: Size,
) -> np.ndarray:
    offset_x = hero_row1_col_offset_x(hero_row1, col)
    return strip[0 : crop_size.h, offset_x : offset_x + crop_size.w]


def scan_hero_row1_cells(
    config: BotConfig,
    hero_template_bgr: np.ndarray,
    row_strip: np.ndarray | None = None,
) -> list[Cell]:
    strip = row_strip if row_strip is not None else capture_hero_row1_strip(config)
    cells: list[Cell] = []

    for col, (center_x, center_y) in enumerate(hero_row1_centers(config.hero_row1)):
        cell_img = crop_hero_row1_cell(strip, config.hero_row1, col, config.slot_crop_size)
        score = match_score(cell_img, hero_template_bgr)
        is_empty = score >= config.hero_empty_threshold
        cells.append(
            Cell(
                row=0,
                col=col,
                center_x=center_x,
                center_y=center_y,
                is_empty=is_empty,
                match_score=score,
            )
        )

    return cells


def find_hero_row1_items(
    config: BotConfig,
    hero_template_bgr: np.ndarray,
    row_strip: np.ndarray | None = None,
) -> list[Cell]:
    cells = scan_hero_row1_cells(config, hero_template_bgr, row_strip)
    return [cell for cell in cells if not cell.is_empty]


def stash_last_slot_score(
    config: BotConfig,
    stash_template_bgr: np.ndarray,
) -> float:
    return slot_match_score(
        config.stash_last_slot.x,
        config.stash_last_slot.y,
        stash_template_bgr,
        config.slot_crop_size,
    )


def is_stash_full(
    config: BotConfig,
    stash_template_bgr: np.ndarray,
) -> bool:
    score = stash_last_slot_score(config, stash_template_bgr)
    return score < config.stash_empty_threshold
