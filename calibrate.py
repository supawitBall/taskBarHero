"""Interactive point-based calibration for hero row 1 and multi-stash tabs."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pyautogui

from grid_utils import BotConfig, HeroRow1, Point, Size, slot_crop_region

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
HERO_BAG_TEMPLATE_PATH = BASE_DIR / "templates" / "hero_bag_empty_slot.png"
STASH_LAST_SLOT_TEMPLATE_PATH = BASE_DIR / "templates" / "stash_last_slot_empty.png"


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


def capture_slot_template(
    center_x: int,
    center_y: int,
    crop_w: int,
    crop_h: int,
    output_path: Path,
) -> None:
    left, top, width, height = slot_crop_region(center_x, center_y, crop_w, crop_h)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image = pyautogui.screenshot(region=(left, top, width, height))
    image.save(output_path)
    print(f"  บันทึก template: {output_path} ({width}x{height}px)")


def load_defaults() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    with CONFIG_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    pyautogui.FAILSAFE = True

    print("=" * 60)
    print("TaskBarHero - Point-based Calibration")
    print("=" * 60)
    print("เตรียมเกมให้พร้อม:")
    print("  - หน้าต่าง STASH (ซ้าย) และ HERO (ขวา) เปิดคู่กัน")
    print("  - Hero row 1 ควรว่าง (ไม่มีไอเทม) ตอนแคป template")
    print("  - Stash ช่องสุดท้ายควรว่าง ตอนแคป template")
    print("  - ขนาดหน้าต่างเกมคงที่ + Windows scaling 100%")
    print("  - ขยับเมาส์ไปมุมจอเพื่อหยุดฉุกเฉิน (FAILSAFE)")
    print()

    countdown = prompt_int("เริ่ม calibrate ใน (วินาที)", 3)
    for remaining in range(countdown, 0, -1):
        print(f"  เริ่มใน {remaining}...")
        time.sleep(1)

    defaults = load_defaults()
    hero_defaults = defaults.get("hero_row1", {})

    try:
        print("\n=== Hero bag row 1 ===")
        print("  สำคัญ: เลือกเฉพาะตารางกระเป๋า row 1 (ไม่รวม equipment)")
        print("  สำคัญ: คลิกกลางช่องที่ 1 และช่องสุดท้ายของ row 1 ให้ตรงเป๊ะ")
        hero_first = wait_for_click("คลิกกลางช่องที่ 1 row 1 ของกระเป๋า Hero")
        hero_last = wait_for_click("คลิกกลางช่องสุดท้าย row 1 ของกระเป๋า Hero")
        hero_cols = prompt_int("Hero row 1 cols (จำนวนช่องในแถว)", hero_defaults.get("cols", 8))

        print("\n  คลิกช่องว่าง row 1 หนึ่งช่องเพื่อแคป hero empty template")
        hero_empty = wait_for_click("คลิกกลางช่องว่าง row 1 ในกระเป๋า Hero")

        crop_w = prompt_int("slot crop width (px)", defaults.get("slot_crop_size", {}).get("w", 40))
        crop_h = prompt_int("slot crop height (px)", defaults.get("slot_crop_size", {}).get("h", 40))
        slot_crop_size = Size(w=crop_w, h=crop_h)

        capture_slot_template(
            hero_empty[0],
            hero_empty[1],
            crop_w,
            crop_h,
            HERO_BAG_TEMPLATE_PATH,
        )

        print("\n=== Stash last slot ===")
        print("  เปิด Stash tab แรก และให้ช่องสุดท้ายว่าง")
        stash_last = wait_for_click("คลิกกลางช่องสุดท้ายของ Stash")
        capture_slot_template(
            stash_last[0],
            stash_last[1],
            crop_w,
            crop_h,
            STASH_LAST_SLOT_TEMPLATE_PATH,
        )

        stash_count = prompt_int(
            "จำนวน Stash (tabs)",
            len(defaults.get("stash_tabs", [])) or 2,
        )
        stash_tabs: list[Point] = []
        for index in range(stash_count):
            tab_pos = wait_for_click(f"คลิกปุ่ม Stash tab {index + 1}")
            stash_tabs.append(Point(x=tab_pos[0], y=tab_pos[1]))

        match_threshold = prompt_float(
            "match_threshold (0-1)",
            defaults.get("match_threshold", 0.85),
        )
        hero_empty_threshold = prompt_float(
            "hero_empty_threshold (score ต่ำกว่านี้ = มี item)",
            defaults.get("hero_empty_threshold", 0.82),
        )
        stash_empty_threshold = prompt_float(
            "stash_empty_threshold (score ต่ำกว่านี้ = Stash เต็ม)",
            defaults.get("stash_empty_threshold", match_threshold),
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
            hero_row1=HeroRow1(
                first_cell=Point(x=hero_first[0], y=hero_first[1]),
                last_cell=Point(x=hero_last[0], y=hero_last[1]),
                cols=hero_cols,
            ),
            stash_last_slot=Point(x=stash_last[0], y=stash_last[1]),
            stash_tabs=stash_tabs,
            hero_bag_empty_slot_template=HERO_BAG_TEMPLATE_PATH,
            stash_last_slot_empty_template=STASH_LAST_SLOT_TEMPLATE_PATH,
            slot_crop_size=slot_crop_size,
            match_threshold=match_threshold,
            hero_empty_threshold=hero_empty_threshold,
            stash_empty_threshold=stash_empty_threshold,
            action_delay_sec=action_delay,
            scan_delay_sec=scan_delay,
            stash_tab_switch_delay_sec=stash_tab_switch_delay,
        )
        config.save(CONFIG_PATH)

        print("\nCalibration เสร็จแล้ว!")
        print(f"  config: {CONFIG_PATH}")
        print(f"  hero template: {HERO_BAG_TEMPLATE_PATH}")
        print(f"  stash last-slot template: {STASH_LAST_SLOT_TEMPLATE_PATH}")
        print(f"  stash tabs: {stash_count} แท็บ")
        print("\nรันบอทด้วย: python bot.py")
        return 0
    except KeyboardInterrupt:
        print("\nยกเลิก calibration")
        return 1


if __name__ == "__main__":
    sys.exit(main())
