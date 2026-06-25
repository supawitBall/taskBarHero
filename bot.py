"""Main bot loop: move items from Hero row 1 to Stash tabs."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pyautogui

from grid_utils import (
    BotConfig,
    find_hero_row1_items,
    load_template_bgr,
    scan_hero_row1_cells,
    stash_last_slot_score,
)

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"

STOP_KEY = "esc"


class StopRequested(Exception):
    pass


def _esc_pressed() -> bool:
    try:
        import keyboard

        return keyboard.is_pressed(STOP_KEY)
    except ImportError:
        pass

    if sys.platform == "win32":
        import msvcrt

        while msvcrt.kbhit():
            if msvcrt.getch() == b"\x1b":
                return True

    return False


def check_stop() -> None:
    if _esc_pressed():
        raise StopRequested()


def validate_config(config: BotConfig) -> None:
    if not config.hero_bag_empty_slot_template.exists():
        raise FileNotFoundError(
            f"ไม่พบ hero template: {config.hero_bag_empty_slot_template}\n"
            "รัน python calibrate.py ก่อน"
        )
    if not config.stash_last_slot_empty_template.exists():
        raise FileNotFoundError(
            f"ไม่พบ stash template: {config.stash_last_slot_empty_template}\n"
            "รัน python calibrate.py ก่อน"
        )
    if config.hero_row1.cols <= 0:
        raise ValueError("hero_row1.cols ต้องมากกว่า 0")
    if not config.stash_tabs:
        raise ValueError("stash_tabs ว่าง — รัน python calibrate.py ใหม่")
    if config.slot_crop_size.w <= 0 or config.slot_crop_size.h <= 0:
        raise ValueError("slot_crop_size ยังไม่ได้ calibrate (w/h = 0)")


def switch_to_stash(index: int, config: BotConfig) -> None:
    tab = config.stash_tabs[index]
    print(f"  → คลิก Stash tab {index + 1} ที่ ({tab.x}, {tab.y})")
    pyautogui.click(tab.x, tab.y)
    time.sleep(config.action_delay_sec)
    time.sleep(config.stash_tab_switch_delay_sec)


def ensure_stash_has_space(
    config: BotConfig,
    stash_template_bgr,
    current_index: int,
) -> tuple[int, bool]:
    while True:
        score = stash_last_slot_score(config, stash_template_bgr)
        is_full = score < config.stash_empty_threshold

        if not is_full:
            print(
                f"Stash tab {current_index + 1} มีที่ว่าง "
                f"(ช่องสุดท้าย score={score:.2f})"
            )
            return current_index, True

        print(
            f"Stash tab {current_index + 1} เต็ม "
            f"(ช่องสุดท้าย score={score:.2f})"
        )

        if current_index >= len(config.stash_tabs) - 1:
            print(" ===== Item เต็มระบบหยุดทำงาน ===== ")
            return current_index, False

        next_index = current_index + 1
        print(f"  → เปลี่ยนไป Stash tab {next_index + 1}")
        switch_to_stash(next_index, config)
        current_index = next_index


def log_hero_row1_scan(config: BotConfig, hero_template_bgr) -> None:
    cells = scan_hero_row1_cells(config, hero_template_bgr)
    print("  สแกน Hero row 1:")
    for cell in cells:
        status = "item" if not cell.is_empty else "ว่าง"
        print(
            f"    ช่อง {cell.col + 1}: score={cell.match_score:.2f} ({status}) "
            f"@ ({cell.center_x}, {cell.center_y})"
        )


def run_bot(config: BotConfig) -> None:
    stash_template_bgr = load_template_bgr(config.stash_last_slot_empty_template)
    hero_template_bgr = load_template_bgr(config.hero_bag_empty_slot_template)
    current_stash_index = 0
    moved_count = 0
    stash_initialized = False

    print("เริ่มทำงาน (กด Esc เพื่อหยุด, ขยับเมาส์มุมจอ = FAILSAFE)")
    print("สแกนเฉพาะ Hero row 1 — ไม่รวม equipment และ row อื่น")
    time.sleep(0.5)

    while True:
        check_stop()

        items = find_hero_row1_items(config, hero_template_bgr)

        if not items:
            print("ไม่พบ item ในกระเป๋า Hero")
            log_hero_row1_scan(config, hero_template_bgr)
            break

        if not stash_initialized:
            switch_to_stash(0, config)
            current_stash_index = 0
            stash_initialized = True

        current_stash_index, has_space = ensure_stash_has_space(
            config,
            stash_template_bgr,
            current_stash_index,
        )
        if not has_space:
            break

        item = items[0]
        print(
            f"Right-click item ใน Hero ช่อง {item.col + 1} "
            f"(score={item.match_score:.2f}) → Stash tab {current_stash_index + 1}"
        )
        pyautogui.rightClick(item.center_x, item.center_y)
        moved_count += 1
        time.sleep(config.action_delay_sec)
        time.sleep(config.scan_delay_sec)


def main() -> int:
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.05

    if not CONFIG_PATH.exists():
        print(f"ไม่พบ {CONFIG_PATH} — รัน python calibrate.py ก่อน")
        return 1

    try:
        config = BotConfig.load(CONFIG_PATH)
        validate_config(config)
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"Config error: {exc}")
        return 1

    print("=" * 60)
    print("TaskBarHero - Stash Transfer Bot")
    print("=" * 60)
    print("เตรียมเกม: เปิด STASH + HERO, มีไอเทมใน Hero row 1")
    print(f"หยุดด้วย: กด {STOP_KEY.upper()} หรือขยับเมาส์ไปมุมจอ")
    print()

    countdown = 3
    for remaining in range(countdown, 0, -1):
        print(f"เริ่มใน {remaining}...")
        time.sleep(1)

    try:
        run_bot(config)
    except StopRequested:
        print("หยุดโดยผู้ใช้ (Esc)")
    except pyautogui.FailSafeException:
        print("หยุดฉุกเฉิน (FAILSAFE)")
    except KeyboardInterrupt:
        print("หยุด (Ctrl+C)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
