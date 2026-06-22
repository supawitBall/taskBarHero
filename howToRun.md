# TaskBarHero — วิธีติดตั้งและใช้งาน / How to Run

บอท PyAutoGUI สำหรับย้ายไอเทมจาก **Hero row 1** ไป **Stash** โดยคลิกขวา  
PyAutoGUI bot that moves items from **Hero row 1** to **Stash** via right-click.

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
**ต้อง calibrate ใหม่** หลังอัปเดตเป็นระบบ point-based

### เตรียมเกมก่อน calibrate

- เปิดหน้าต่าง **STASH** (ซ้าย) และ **HERO** (ขวา) คู่กัน
- Hero **row 1 ว่าง** (ไม่มีไอเทม) ตอนแคป template
- Stash **ช่องสุดท้ายว่าง** ตอนแคป template
- ห้ามย่อ/ขยายหรือขยับหน้าต่างเกมระหว่าง calibrate

```cmd
venv\Scripts\activate
python calibrate.py
```

### ขั้นตอนใน calibrate

| ลำดับ | ทำอะไร |
|-------|--------|
| 1 | คลิกกลาง **ช่องแรก row 1** ของกระเป๋า Hero (ไม่รวม equipment) |
| 2 | คลิกกลาง **ช่องสุดท้าย row 1** ของกระเป๋า Hero |
| 3 | ใส่จำนวน **cols** ของ row 1 (default 8) |
| 4 | คลิกช่องว่าง row 1 เพื่อแคป hero template |
| 5 | ใส่ขนาด crop (width/height px, default 40) |
| 6 | คลิกกลาง **ช่องสุดท้ายของ Stash** (ขณะช่องว่าง) |
| 7 | ใส่ **จำนวน Stash** (เช่น 2, 3, ...) |
| 8 | คลิกปุ่ม Stash แต่ละแท็บตามลำดับ (Tab 1, Tab 2, ...) |
| 9 | ใส่ `match_threshold`, `action_delay_sec`, `scan_delay_sec` |

ไฟล์ที่ได้หลัง calibrate:

- `config.json`
- `templates/hero_bag_empty_slot.png`
- `templates/stash_last_slot_empty.png`

---

## 4. รันบอท / Run the bot

### เตรียมเกม

- เปิด **STASH + HERO**
- มีไอเทมใน **Hero row 1** เท่านั้น (row อื่นไม่ถูกย้าย)
- อย่าขยับหน้าต่างเกมระหว่างบอททำงาน

```cmd
venv\Scripts\activate
python bot.py
```

มี **countdown 3 วินาที** ก่อนเริ่ม — ใช้เวลานี้สลับไปหน้าต่างเกม

### บอททำอะไร

1. สแกน **Hero row 1** หาไอเทม
2. ไม่พบ item → log `"ไม่พบ item ในกระเป๋า Hero"` แล้วหยุด (ไม่คลิก)
3. มี item → คลิก Stash tab แรก แล้วเช็ก **ช่องสุดท้ายของ Stash** ว่าว่างไหม
4. ช่องสุดท้ายไม่ว่าง (Stash เต็ม) → เปลี่ยนไป Stash tab ถัดไป
5. Stash สุดท้ายเต็ม → log `" ===== Item เต็มระบบหยุดทำงาน ===== "` แล้วหยุด
6. คลิกขวาไอเทมทีละชิ้นเพื่อย้ายไป Stash แล้ววนซ้ำ

---

## 5. วิธีหยุด / How to stop

| วิธี | การทำงาน |
|------|----------|
| **Esc** | กด `Esc` ขณะบอททำงาน → หยุดอย่างปลอดภัย |
| **FAILSAFE** | ขยับเมาส์ไป **มุมซ้ายบนสุดของจอ** อย่างรวดเร็ว → หยุดฉุกเฉิน |
| **Ctrl+C** | กดใน terminal ที่รัน `bot.py` |

บอทหยุดเองเมื่อ:

- ไม่พบ item ใน Hero row 1
- Stash ทุกแท็บที่ตั้งค่าไว้ **เต็ม** (ช่องสุดท้ายไม่ว่าง)

---

## 6. แก้ปัญหาเบื้องต้น / Troubleshooting

| อาการ | แนวทางแก้ |
|-------|-----------|
| `AttributeError: ... isKeyDown` | รัน `pip install -r requirements.txt` ใหม่ (ต้องมี package `keyboard`) |
| `Config error: ไม่พบ template` | รัน `python calibrate.py` ก่อน |
| `slot_crop_size ยังไม่ได้ calibrate` | รัน `python calibrate.py` ใหม่ |
| `stash_tabs ว่าง` | รัน `python calibrate.py` ใหม่ |
| บอทคลิกผิดตำแหน่ง | calibrate ใหม่, ตั้ง scaling 100%, ห้ามย่อหน้าต่างเกม |
| บอทมองช่องว่างเป็นไอเทม (หรือกลับกัน) | calibrate ใหม่ หรือปรับ `match_threshold` ใน `config.json` (เช่น `0.80`) |
| Stash สลับเร็วเกินไป | เพิ่ม `action_delay_sec` ใน `config.json` |

---

## โครงสร้างไฟล์สำคัญ / Key files

```
taskBarHero/
├── calibrate.py      # กำหนดพิกัดจุด + template
├── bot.py            # รันบอท
├── config.json       # พิกัดจาก calibrate
├── requirements.txt
├── howToRun.md       # ไฟล์นี้
└── templates/
    ├── hero_bag_empty_slot.png
    └── stash_last_slot_empty.png
```

---

## คำเตือน / Disclaimer

การใช้ automation อาจขัดกับข้อกำหนดของเกม ใช้ด้วยความเสี่ยงของตัวเอง  
Using automation may violate the game's terms of service — use at your own risk.
