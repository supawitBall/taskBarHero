"""Main bot loop: move items from Hero slots to Stash tabs using color detection."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pyautogui

from grid_utils import (
    HERO_SLOT_COUNT,
    STASH_TAB_COUNT,
    BotConfig,
    color_distance,
    find_hero_items,
    stash_last_slot_color,
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
    if len(config.hero_slots) != HERO_SLOT_COUNT:
        raise ValueError(f"hero_slots ต้องมี {HERO_SLOT_COUNT} ช่อง — รัน python calibrate.py ใหม่")
    if len(config.stash_tabs) != STASH_TAB_COUNT:
        raise ValueError(f"stash_tabs ต้องมี {STASH_TAB_COUNT} แท็บ — รัน python calibrate.py ใหม่")
    for index, slot in enumerate(config.hero_slots, start=1):
        if slot.x <= 0 and slot.y <= 0:
            raise ValueError(f"hero slot {index} ยังไม่ได้ calibrate")
    if config.stash_last_slot.x <= 0 and config.stash_last_slot.y <= 0:
        raise ValueError("stash_last_slot ยังไม่ได้ calibrate")


def switch_to_stash(index: int, config: BotConfig) -> None:
    tab = config.stash_tabs[index]
    print(f"  → คลิก Stash tab {index + 1} ที่ ({tab.x}, {tab.y})")
    pyautogui.click(tab.x, tab.y)
    time.sleep(config.action_delay_sec)
    time.sleep(config.stash_tab_switch_delay_sec)


def is_final_stash_full(config: BotConfig) -> bool:
    """Return True when the last slot on the final stash tab is full."""
    last_index = len(config.stash_tabs) - 1
    switch_to_stash(last_index, config)
    current_color = stash_last_slot_color(config)
    dist = color_distance(current_color, config.empty_slot_color)
    is_full = dist > config.color_tolerance
    if is_full:
        print(
            f"Stash tab {last_index + 1} (สุดท้าย) เต็ม "
            f"({current_color} ≠ empty {config.empty_slot_color}, dist={dist:.1f})"
        )
    return is_full


def ensure_stash_has_space(config: BotConfig, current_index: int) -> tuple[int, bool]:
    while True:
        current_color = stash_last_slot_color(config)
        dist = color_distance(current_color, config.empty_slot_color)
        stash_is_full = dist > config.color_tolerance

        if not stash_is_full:
            print(
                f"Stash tab {current_index + 1} มีที่ว่าง "
                f"({current_color} ≈ empty {config.empty_slot_color}, dist={dist:.1f})"
            )
            return current_index, True

        print(
            f"Stash tab {current_index + 1} เต็ม "
            f"({current_color} ≠ empty {config.empty_slot_color}, dist={dist:.1f})"
        )

        if current_index >= len(config.stash_tabs) - 1:
            print(" ===== Item เต็มระบบหยุดทำงาน ===== ")
            return current_index, False

        next_index = current_index + 1
        print(f"  → เปลี่ยนไป Stash tab {next_index + 1}")
        switch_to_stash(next_index, config)
        current_index = next_index


def run_bot(config: BotConfig) -> None:
    current_stash_index = 0
    stash_initialized = False

    print("เริ่มทำงาน (กด Esc เพื่อหยุด, ขยับเมาส์มุมจอ = FAILSAFE)")
    print("หยุดอัตโนมัติเฉพาะเมื่อ Stash tab สุดท้ายเต็ม")
    print(f"empty color: {config.empty_slot_color}, tolerance: {config.color_tolerance}")
    time.sleep(0.5)

    while True:
        check_stop()

        items = find_hero_items(config)

        if not items:
            print("ไม่พบ item ในกระเป๋า Hero — รอ scan...")
            if is_final_stash_full(config):
                print(" ===== Item เต็มระบบหยุดทำงาน ===== ")
                break
            time.sleep(config.scan_delay_sec)
            continue

        if not stash_initialized:
            switch_to_stash(0, config)
            current_stash_index = 0
            stash_initialized = True

        current_stash_index, has_space = ensure_stash_has_space(
            config,
            current_stash_index,
        )
        if not has_space:
            break

        item = items[0]
        print(
            f"Right-click item ใน Hero ช่อง {item.col + 1} "
            f"({item.color}) → Stash tab {current_stash_index + 1}"
        )
        pyautogui.rightClick(item.center_x, item.center_y)
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
    print("TaskBarHero - Stash Transfer Bot (Color-based)")
    print("=" * 60)
    print("เตรียมเกม: เปิด STASH + HERO (บอทจะรอ item ใน Hero ช่อง 1-7)")
    print("หยุดอัตโนมัติ: Stash tab สุดท้ายเต็ม | หยุดเอง: Esc / FAILSAFE / Ctrl+C")
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
