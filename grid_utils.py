"""Color-based slot detection for hero slots and stash last slot."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pyautogui


HERO_SLOT_COUNT = 7
STASH_TAB_COUNT = 3


@dataclass(frozen=True)
class Point:
    x: int
    y: int

    @classmethod
    def from_dict(cls, data: dict[str, int]) -> "Point":
        return cls(x=data["x"], y=data["y"])


@dataclass(frozen=True)
class RGBColor:
    r: int
    g: int
    b: int

    @classmethod
    def from_dict(cls, data: dict[str, int]) -> "RGBColor":
        return cls(r=data["r"], g=data["g"], b=data["b"])

    def __str__(self) -> str:
        return f"RGB({self.r}, {self.g}, {self.b})"


@dataclass(frozen=True)
class Cell:
    row: int
    col: int
    center_x: int
    center_y: int
    is_empty: bool
    color: RGBColor
    color_distance: float


@dataclass
class BotConfig:
    hero_slots: list[Point]
    stash_last_slot: Point
    stash_tabs: list[Point]
    empty_slot_color: RGBColor
    color_tolerance: float
    sample_size: int
    action_delay_sec: float
    scan_delay_sec: float
    stash_tab_switch_delay_sec: float

    @classmethod
    def load(cls, config_path: str | Path) -> "BotConfig":
        path = Path(config_path)
        with path.open(encoding="utf-8") as f:
            data = json.load(f)

        return cls(
            hero_slots=[Point.from_dict(slot) for slot in data["hero_slots"]],
            stash_last_slot=Point.from_dict(data["stash_last_slot"]),
            stash_tabs=[Point.from_dict(tab) for tab in data["stash_tabs"]],
            empty_slot_color=RGBColor.from_dict(data["empty_slot_color"]),
            color_tolerance=float(data.get("color_tolerance", 15)),
            sample_size=int(data.get("sample_size", 5)),
            action_delay_sec=float(data.get("action_delay_sec", 0.25)),
            scan_delay_sec=float(data.get("scan_delay_sec", 0.1)),
            stash_tab_switch_delay_sec=float(data.get("stash_tab_switch_delay_sec", 0.6)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "hero_slots": [{"x": slot.x, "y": slot.y} for slot in self.hero_slots],
            "stash_last_slot": {"x": self.stash_last_slot.x, "y": self.stash_last_slot.y},
            "stash_tabs": [{"x": tab.x, "y": tab.y} for tab in self.stash_tabs],
            "empty_slot_color": {
                "r": self.empty_slot_color.r,
                "g": self.empty_slot_color.g,
                "b": self.empty_slot_color.b,
            },
            "color_tolerance": self.color_tolerance,
            "sample_size": self.sample_size,
            "action_delay_sec": self.action_delay_sec,
            "scan_delay_sec": self.scan_delay_sec,
            "stash_tab_switch_delay_sec": self.stash_tab_switch_delay_sec,
        }

    def save(self, config_path: str | Path) -> None:
        path = Path(config_path)
        with path.open("w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
            f.write("\n")


def sample_region(left: int, top: int, width: int, height: int) -> np.ndarray:
    screenshot = pyautogui.screenshot(region=(left, top, width, height))
    return np.array(screenshot.convert("RGB"))


def sample_slot_color(x: int, y: int, sample_size: int = 5) -> RGBColor:
    half = sample_size // 2
    left = x - half
    top = y - half
    pixels = sample_region(left, top, sample_size, sample_size)
    mean = pixels.mean(axis=(0, 1))
    return RGBColor(r=int(round(mean[0])), g=int(round(mean[1])), b=int(round(mean[2])))


def color_distance(a: RGBColor, b: RGBColor) -> float:
    return math.sqrt((a.r - b.r) ** 2 + (a.g - b.g) ** 2 + (a.b - b.b) ** 2)


def is_same_empty_color(current: RGBColor, reference: RGBColor, tolerance: float) -> bool:
    return color_distance(current, reference) <= tolerance


def scan_hero_cells(config: BotConfig) -> list[Cell]:
    cells: list[Cell] = []
    for col, slot in enumerate(config.hero_slots):
        current_color = sample_slot_color(slot.x, slot.y, config.sample_size)
        distance = color_distance(current_color, config.empty_slot_color)
        is_empty = distance <= config.color_tolerance
        cells.append(
            Cell(
                row=0,
                col=col,
                center_x=slot.x,
                center_y=slot.y,
                is_empty=is_empty,
                color=current_color,
                color_distance=distance,
            )
        )
    return cells


def find_hero_items(config: BotConfig) -> list[Cell]:
    return [cell for cell in scan_hero_cells(config) if not cell.is_empty]


def stash_last_slot_color(config: BotConfig) -> RGBColor:
    return sample_slot_color(
        config.stash_last_slot.x,
        config.stash_last_slot.y,
        config.sample_size,
    )


def is_stash_full(config: BotConfig) -> bool:
    current = stash_last_slot_color(config)
    return not is_same_empty_color(
        current,
        config.empty_slot_color,
        config.color_tolerance,
    )
