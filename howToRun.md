# TaskBarHero — วิธีติดตั้งและใช้งาน / How to Run

บอท PyAutoGUI สำหรับย้ายไอเทมจาก **กระเป๋า Hero** ไป **Stash** โดยคลิกขวา  
PyAutoGUI bot that moves items from the **Hero bag** to **Stash** via right-click.

---

## ความต้องการของระบบ / Requirements

- **Windows** (เครื่องที่เล่นเกม)
- **Python 3.10+** — ดาวน์โหลดจาก [python.org](https://www.python.org/downloads/)  
  ตอนติดตั้งให้ติ๊ก **Add Python to PATH**
- เกมรันแบบ **windowed / borderless** ขนาดหน้าต่างคงที่
- Windows display scaling **100%**

---

## 1. Clone โปรเจกต์ / Clone the project

```cmd
git clone <url-of-repo> taskBarHero
cd taskBarHero
```

---

## 2. ติดตั้ง dependencies / Install dependencies

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

> ทุกครั้งที่เปิด terminal ใหม่ ต้อง `venv\Scripts\activate` ก่อนรันสคริปต์  
> Each new terminal session: run `venv\Scripts\activate` first.

---

## 3. Calibrate (ครั้งแรก / เปลี่ยน resolution)

รัน **ก่อนใช้บอทครั้งแรก** หรือเมื่อเปลี่ยนขนาดหน้าต่างเกม

### เตรียมเกมก่อน calibrate

- เปิดหน้าต่าง **STASH** (ซ้าย) และ **HERO** (ขวา) คู่กัน
- Stash อยู่ **Tab 1**
- กระเป๋า Hero **ว่าง** (ไม่มีไอเทม) ตอนแคป template
- ห้ามย่อ/ขยายหรือขยับหน้าต่างเกมระหว่าง calibrate

```cmd
venv\Scripts\activate
python calibrate.py
```

### ขั้นตอนใน calibrate

| ลำดับ | ทำอะไร |
|-------|--------|
| 1 | คลิกมุมซ้ายบน + ขวาล่างของ **ตาราง Stash** (ไม่รวมแท็บ) |
| 2 | คลิกมุมซ้ายบน + ขวาล่างของ **ตารางกระเป๋า Hero เท่านั้น** (ใต้ equipment — **ห้ามรวมช่องของสวมใส่**) |
| 3 | คลิกปุ่ม **Stash Tab 1** |
| 4 | คลิกปุ่ม **Stash Tab 2** |
| 5 | คลิกกลาง **ช่องว่างใน Stash tab 1** → สร้าง `templates/stash_empty_slot.png` |
| 6 | คลิกกลาง **ช่องว่างในกระเป๋า Hero** → สร้าง `templates/hero_bag_empty_slot.png` |
| 7 | ใส่ rows/cols (กด Enter ใช้ค่า default ได้) |
| 8 | ใส่ `match_threshold`, `action_delay_sec`, `scan_delay_sec` |

ไฟล์ที่ได้หลัง calibrate:

- `config.json`
- `templates/stash_empty_slot.png`
- `templates/hero_bag_empty_slot.png`

---

## 4. รันบอท / Run the bot

### เตรียมเกม

- เปิด **STASH + HERO**
- มีไอเทมใน **กระเป๋า Hero** (ไม่ใช่ equipment)
- อย่าขยับหน้าต่างเกมระหว่างบอททำงาน

```cmd
venv\Scripts\activate
python bot.py
```

มี **countdown 3 วินาที** ก่อนเริ่ม — ใช้เวลานี้สลับไปหน้าต่างเกม

### บอททำอะไร

1. สแกนกระเป๋า Hero หาไอเทม
2. เช็ก Stash tab ปัจจุบันว่ามีช่องว่างไหม
3. Tab 1 เต็ม → เปลี่ยน Tab 2
4. Tab 2 เต็ม → หยุด
5. คลิกขวาไอเทมทีละชิ้นเพื่อย้ายไป Stash
6. วนซ้ำจนกระเป๋าว่างหรือคลังเต็ม

---

## 5. วิธีหยุด / How to stop

| วิธี | การทำงาน |
|------|----------|
| **Esc** | กด `Esc` ขณะบอททำงาน → หยุดอย่างปลอดภัย |
| **FAILSAFE** | ขยับเมาส์ไป **มุมซ้ายบนสุดของจอ** อย่างรวดเร็ว → หยุดฉุกเฉิน |
| **Ctrl+C** | กดใน terminal ที่รัน `bot.py` |

บอทหยุดเองเมื่อ:

- กระเป๋า Hero **ว่าง**
- Stash **Tab 1 + Tab 2 เต็ม**

---

## 6. แก้ปัญหาเบื้องต้น / Troubleshooting

| อาการ | แนวทางแก้ |
|-------|-----------|
| `AttributeError: ... isKeyDown` | รัน `pip install -r requirements.txt` ใหม่ (ต้องมี package `keyboard`) |
| `Config error: ไม่พบ template` | รัน `python calibrate.py` ก่อน |
| `ยังไม่ได้ calibrate (w/h = 0)` | รัน `python calibrate.py` ใหม่ |
| บอทคลิกผิดตำแหน่ง | calibrate ใหม่, ตั้ง scaling 100%, ห้ามย่อหน้าต่างเกม |
| บอทมองช่องว่างเป็นไอเทม (หรือกลับกัน) | calibrate ใหม่ หรือปรับ `match_threshold` ใน `config.json` (เช่น `0.80`) |
| บอทคลิก equipment | calibrate `hero_bag_roi` ใหม่ — เลือกเฉพาะตารางกระเป๋า |

---

## โครงสร้างไฟล์สำคัญ / Key files

```
taskBarHero/
├── calibrate.py      # กำหนด ROI + template
├── bot.py            # รันบอท
├── config.json       # พิกัดจาก calibrate
├── requirements.txt
├── howToRun.md       # ไฟล์นี้
└── templates/
    ├── stash_empty_slot.png
    └── hero_bag_empty_slot.png
```

---

## คำเตือน / Disclaimer

การใช้ automation อาจขัดกับข้อกำหนดของเกม ใช้ด้วยความเสี่ยงของตัวเอง  
Using automation may violate the game's terms of service — use at your own risk.
