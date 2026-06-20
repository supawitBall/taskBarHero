"""Main bot loop: move items from Hero bag to Stash."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pyautogui

from grid_utils import BotConfig, count_empty_cells, find_bag_item_cells, load_template_bgr

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
    if not config.stash_empty_slot_template.exists():
        raise FileNotFoundError(
            f"ไม่พบ stash template: {config.stash_empty_slot_template}\n"
            "รัน python calibrate.py ก่อน"
        )
    if not config.hero_bag_empty_slot_template.exists():
        raise FileNotFoundError(
            f"ไม่พบ hero bag template: {config.hero_bag_empty_slot_template}\n"
            "รัน python calibrate.py ก่อน"
        )
    for name, roi in [
        ("stash_roi", config.stash_roi),
        ("hero_bag_roi", config.hero_bag_roi),
    ]:
        if roi.w <= 0 or roi.h <= 0:
            raise ValueError(f"{name} ยังไม่ได้ calibrate (w/h = 0)")


def switch_to_tab(tab: int, config: BotConfig) -> None:
    x, y = config.tab1 if tab == 1 else config.tab2
    pyautogui.click(x, y)
    time.sleep(config.action_delay_sec)


def ensure_stash_has_space(config: BotConfig, template_bgr, current_tab: int) -> tuple[int, bool]:
    """Return (active_tab, has_space). Switch to tab 2 if tab 1 is full."""
    empty_count = count_empty_cells(
        config.stash_roi,
        config.stash_grid,
        template_bgr,
        config.match_threshold,
    )

    if empty_count > 0:
        return current_tab, True

    if current_tab == 1:
        print("Tab 1 เต็ม → เปลี่ยนไป Tab 2")
        switch_to_tab(2, config)
        current_tab = 2
        empty_count = count_empty_cells(
            config.stash_roi,
            config.stash_grid,
            template_bgr,
            config.match_threshold,
        )

    if empty_count == 0:
        print("Tab 2 เต็ม → หยุดบอท")
        return current_tab, False

    return current_tab, True


def run_bot(config: BotConfig) -> None:
    stash_template_bgr = load_template_bgr(config.stash_empty_slot_template)
    hero_bag_template_bgr = load_template_bgr(config.hero_bag_empty_slot_template)
    current_tab = 1
    moved_count = 0

    print("เริ่มทำงาน (กด Esc เพื่อหยุด, ขยับเมาส์มุมจอ = FAILSAFE)")
    print("สแกนเฉพาะตารางกระเป๋า Hero — ไม่รวมช่อง equipment")
    switch_to_tab(1, config)
    current_tab = 1
    time.sleep(0.5)

    while True:
        check_stop()

        items = find_bag_item_cells(
            config.hero_bag_roi,
            config.hero_bag_grid,
            hero_bag_template_bgr,
            config.match_threshold,
        )

        if not items:
            print(f"กระเป๋า Hero ว่าง → หยุด (ย้ายไปแล้ว {moved_count} ชิ้น)")
            break

        current_tab, has_space = ensure_stash_has_space(
            config, stash_template_bgr, current_tab
        )
        if not has_space:
            break

        item = items[0]
        print(
            f"Right-click item ในกระเป๋า Hero row={item.row}, col={item.col} "
            f"(score={item.match_score:.2f}) → Stash tab {current_tab}"
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
    print("เตรียมเกม: เปิด STASH + HERO, มีไอเทมในกระเป๋า Hero (ไม่ใช่ equipment)")
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
