"""Interactive color-based calibration for hero slots and stash tabs."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pyautogui

from grid_utils import (
    HERO_SLOT_COUNT,
    STASH_TAB_COUNT,
    BotConfig,
    Point,
    sample_slot_color,
)

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"


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
            value = int(raw)
            if value <= 0:
                print("กรุณาใส่ตัวเลขที่มากกว่า 0")
                continue
            return value
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


def load_defaults() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    with CONFIG_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    pyautogui.FAILSAFE = True

    print("=" * 60)
    print("TaskBarHero - Color-based Calibration")
    print("=" * 60)
    print("เตรียมเกมให้พร้อม:")
    print("  - หน้าต่าง STASH (ซ้าย) และ HERO (ขวา) เปิดคู่กัน")
    print("  - มีช่องว่างอย่างน้อย 1 ช่อง สำหรับเก็บสี")
    print("  - ขนาดหน้าต่างเกมคงที่ + Windows scaling 100%")
    print("  - ขยับเมาส์ไปมุมจอเพื่อหยุดฉุกเฉิน (FAILSAFE)")
    print()

    countdown = prompt_int("เริ่ม calibrate ใน (วินาที)", 3)
    for remaining in range(countdown, 0, -1):
        print(f"  เริ่มใน {remaining}...")
        time.sleep(1)

    defaults = load_defaults()

    try:
        print("\n=== Hero ช่อง 1-7 ===")
        print("  สำคัญ: คลิกกลางช่อง row 1 ของกระเป๋า Hero (ไม่รวม equipment)")
        hero_slots: list[Point] = []
        for slot_num in range(1, HERO_SLOT_COUNT + 1):
            pos = wait_for_click(f"คลิกกลาง Hero ช่อง {slot_num}")
            hero_slots.append(Point(x=pos[0], y=pos[1]))

        print("\n=== Stash ช่องสุดท้าย ===")
        stash_last = wait_for_click("คลิกกลางช่องสุดท้ายของ Stash")

        print("\n=== Stash tab 1-3 ===")
        stash_tabs: list[Point] = []
        for tab_num in range(1, STASH_TAB_COUNT + 1):
            pos = wait_for_click(f"คลิก Stash tab {tab_num}")
            stash_tabs.append(Point(x=pos[0], y=pos[1]))

        print("\n=== สีช่องว่าง ===")
        print("  คลิกกลางช่องว่าง (Hero หรือ Stash) เพื่อเก็บสี reference")
        empty_pos = wait_for_click("คลิกกลางช่องว่าง")
        sample_size = prompt_int("sample_size (px)", defaults.get("sample_size", 5))
        empty_color = sample_slot_color(empty_pos[0], empty_pos[1], sample_size)
        print(f"  บันทึกสีช่องว่าง: {empty_color}")

        color_tolerance = prompt_float(
            "color_tolerance (ยิ่งสูงยิ่งยอมรับสีใกล้เคียง)",
            defaults.get("color_tolerance", 15),
        )
        action_delay = prompt_float(
            "action_delay_sec",
            defaults.get("action_delay_sec", 0.25),
        )
        scan_delay = prompt_float(
            "scan_delay_sec",
            defaults.get("scan_delay_sec", 0.1),
        )
        stash_tab_switch_delay = prompt_float(
            "stash_tab_switch_delay_sec (รอ UI หลังเปลี่ยน tab)",
            defaults.get("stash_tab_switch_delay_sec", 0.6),
        )

        config = BotConfig(
            hero_slots=hero_slots,
            stash_last_slot=Point(x=stash_last[0], y=stash_last[1]),
            stash_tabs=stash_tabs,
            empty_slot_color=empty_color,
            color_tolerance=color_tolerance,
            sample_size=sample_size,
            action_delay_sec=action_delay,
            scan_delay_sec=scan_delay,
            stash_tab_switch_delay_sec=stash_tab_switch_delay,
        )
        config.save(CONFIG_PATH)

        print("\nCalibration เสร็จแล้ว!")
        print(f"  config: {CONFIG_PATH}")
        print(f"  hero slots: {HERO_SLOT_COUNT} ช่อง")
        print(f"  stash tabs: {STASH_TAB_COUNT} แท็บ")
        print(f"  empty color: {empty_color}")
        print("\nรันบอทด้วย: python bot.py")
        return 0
    except KeyboardInterrupt:
        print("\nยกเลิก calibration")
        return 1


if __name__ == "__main__":
    sys.exit(main())
