"""Interactive calibration tool for ROI, tabs, and empty-slot template."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pyautogui

from grid_utils import BotConfig, GridSpec, ROI, cell_bounds

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
STASH_TEMPLATE_PATH = BASE_DIR / "templates" / "stash_empty_slot.png"
HERO_BAG_TEMPLATE_PATH = BASE_DIR / "templates" / "hero_bag_empty_slot.png"


def prompt(text: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default is not None else ""
    value = input(f"{text}{suffix}: ").strip()
    if not value and default is not None:
        return default
    return value


def prompt_int(text: str, default: int) -> int:
    while True:
        raw = prompt(text, str(default))
        try:
            return int(raw)
        except ValueError:
            print("กรุณาใส่ตัวเลข")


def prompt_float(text: str, default: float) -> float:
    while True:
        raw = prompt(text, str(default))
        try:
            return float(raw)
        except ValueError:
            print("กรุณาใส่ตัวเลข")


def wait_for_click(label: str) -> tuple[int, int]:
    print(f"\n{label}")
    print("  นำเมาส์ไปตำแหน่งที่ต้องการ แล้วกด Enter")
    input("  Enter = บันทึกพิกัด: ")
    pos = pyautogui.position()
    print(f"  บันทึกแล้ว: ({pos.x}, {pos.y})")
    return pos.x, pos.y


def capture_roi(label: str) -> ROI:
    print(f"\n=== {label} ===")
    x1, y1 = wait_for_click("คลิกมุมซ้ายบนของตาราง")
    x2, y2 = wait_for_click("คลิกมุมขวาล่างของตาราง")
    x = min(x1, x2)
    y = min(y1, y2)
    w = abs(x2 - x1)
    h = abs(y2 - y1)
    if w <= 0 or h <= 0:
        raise ValueError(f"ROI ไม่ถูกต้อง: w={w}, h={h}")
    roi = ROI(x=x, y=y, w=w, h=h)
    print(f"  ROI = x={roi.x}, y={roi.y}, w={roi.w}, h={roi.h}")
    return roi


def capture_empty_slot_template(
    roi: ROI,
    grid: GridSpec,
    output_path: Path,
    label: str,
) -> None:
    print(f"\n=== {label} ===")
    slot_x, slot_y = wait_for_click(f"คลิกกลางช่องว่างใน {label}")

    cell_w = roi.w / grid.cols
    cell_h = roi.h / grid.rows
    rel_x = slot_x - roi.x
    rel_y = slot_y - roi.y
    col = min(max(int(rel_x / cell_w), 0), grid.cols - 1)
    row = min(max(int(rel_y / cell_h), 0), grid.rows - 1)

    x0, y0, x1, y1 = cell_bounds(roi, grid, row, col)
    left = roi.x + x0
    top = roi.y + y0
    width = max(x1 - x0, 1)
    height = max(y1 - y0, 1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image = pyautogui.screenshot(region=(left, top, width, height))
    image.save(output_path)
    print(
        f"  บันทึก template แล้ว: {output_path} "
        f"({width}x{height}px, cell row={row}, col={col})"
    )


def load_defaults() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    with CONFIG_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    pyautogui.FAILSAFE = True

    print("=" * 60)
    print("TaskBarHero - Calibration")
    print("=" * 60)
    print("เตรียมเกมให้พร้อม:")
    print("  - หน้าต่าง STASH (ซ้าย) และ HERO (ขวา) เปิดคู่กัน")
    print("  - Stash อยู่ tab 1")
    print("  - Hero bag ควรว่าง (ไม่มีไอเทมในกระเป๋า) ตอนแคป template")
    print("  - ขนาดหน้าต่างเกมคงที่ + Windows scaling 100%")
    print("  - ขยับเมาส์ไปมุมจอเพื่อหยุดฉุกเฉิน (FAILSAFE)")
    print()

    countdown = prompt_int("เริ่ม calibrate ใน (วินาที)", 3)
    for remaining in range(countdown, 0, -1):
        print(f"  เริ่มใน {remaining}...")
        time.sleep(1)

    defaults = load_defaults()

    try:
        stash_roi = capture_roi("Stash grid ROI")
        print("\n=== Hero bag ROI ===")
        print("  สำคัญ: เลือกเฉพาะตารางกระเป๋า (ใต้ equipment)")
        print("  ห้ามรวมช่องของสวมใส่/อาวุธที่ล้อมรอบตัวละคร")
        hero_bag_roi = capture_roi("Hero bag ROI (เฉพาะตารางกระเป๋า)")
        tab1 = wait_for_click("คลิกปุ่ม Stash Tab 1")
        tab2 = wait_for_click("คลิกปุ่ม Stash Tab 2")

        stash_rows = prompt_int("Stash rows", defaults.get("stash_grid", {}).get("rows", 10))
        stash_cols = prompt_int("Stash cols", defaults.get("stash_grid", {}).get("cols", 8))
        hero_rows = prompt_int(
            "Hero bag rows",
            defaults.get("hero_bag_grid", defaults.get("hero_grid", {})).get("rows", 5),
        )
        hero_cols = prompt_int(
            "Hero bag cols",
            defaults.get("hero_bag_grid", defaults.get("hero_grid", {})).get("cols", 8),
        )

        stash_grid = GridSpec(rows=stash_rows, cols=stash_cols)
        hero_bag_grid = GridSpec(rows=hero_rows, cols=hero_cols)

        print("\n  เปิด Stash tab 1 และให้มีช่องว่างอย่างน้อย 1 ช่อง")
        capture_empty_slot_template(
            stash_roi,
            stash_grid,
            STASH_TEMPLATE_PATH,
            "Stash empty slot template",
        )
        capture_empty_slot_template(
            hero_bag_roi,
            hero_bag_grid,
            HERO_BAG_TEMPLATE_PATH,
            "Hero bag empty slot template",
        )

        match_threshold = prompt_float(
            "match_threshold (0-1)",
            defaults.get("match_threshold", 0.85),
        )
        action_delay = prompt_float(
            "action_delay_sec",
            defaults.get("action_delay_sec", 0.25),
        )
        scan_delay = prompt_float(
            "scan_delay_sec",
            defaults.get("scan_delay_sec", 0.1),
        )

        config = BotConfig(
            stash_roi=stash_roi,
            hero_bag_roi=hero_bag_roi,
            tab1=tab1,
            tab2=tab2,
            stash_grid=stash_grid,
            hero_bag_grid=hero_bag_grid,
            stash_empty_slot_template=STASH_TEMPLATE_PATH,
            hero_bag_empty_slot_template=HERO_BAG_TEMPLATE_PATH,
            match_threshold=match_threshold,
            action_delay_sec=action_delay,
            scan_delay_sec=scan_delay,
        )
        config.save(CONFIG_PATH)

        print("\nCalibration เสร็จแล้ว!")
        print(f"  config: {CONFIG_PATH}")
        print(f"  stash template: {STASH_TEMPLATE_PATH}")
        print(f"  hero bag template: {HERO_BAG_TEMPLATE_PATH}")
        print("\nรันบอทด้วย: python bot.py")
        return 0
    except KeyboardInterrupt:
        print("\nยกเลิก calibration")
        return 1


if __name__ == "__main__":
    sys.exit(main())
