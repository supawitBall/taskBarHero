# TaskBarHero — วิธีติดตั้งและใช้งาน / How to Run

บอท PyAutoGUI สำหรับย้ายไอเทมจาก **Hero ช่อง 1–7** ไป **Stash** โดยคลิกขวา  
ใช้ **การเปรียบเทียบสี** ตรวจจับช่องว่างและช่องที่มี item

---

## ความต้องการของระบบ / Requirements

- **Windows** (เครื่องที่เล่นเกม)
- **Python 3.10+** — [python.org](https://www.python.org/downloads/) (ติ๊ก Add Python to PATH)
- เกมรันแบบ **windowed / borderless** ขนาดหน้าต่างคงที่
- Windows display scaling **100%**

---

## 1. Clone และติดตั้ง

```cmd
git clone <url-of-repo> taskBarHero
cd taskBarHero
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## 2. Calibrate (ครั้งแรก / เปลี่ยน resolution)

**ต้อง calibrate ใหม่** หลังอัปเดตเป็นระบบ color-based

### เตรียมเกม

- เปิด **STASH + HERO**
- มีช่องว่างอย่างน้อย 1 ช่อง สำหรับเก็บสี reference

```cmd
venv\Scripts\activate
python calibrate.py
```

### ขั้นตอน calibrate

| ลำดับ | ทำอะไร |
|-------|--------|
| 1 | คลิกกลาง **Hero ช่อง 1** ถึง **ช่อง 7** (7 ครั้ง) |
| 2 | คลิกกลาง **Stash ช่องสุดท้าย** |
| 3 | คลิก **Stash tab 1, 2, 3** |
| 4 | คลิก **ช่องว่าง** เพื่อเก็บสี reference |
| 5 | ใส่ `sample_size`, `color_tolerance`, delays |

ผลลัพธ์: `config.json` พร้อมพิกัดและสี `empty_slot_color`

---

## 3. รันบอท

```cmd
venv\Scripts\activate
python bot.py
```

### Logic การทำงาน

1. สแกน Hero ช่อง 1–7 — สีไม่ตรง `empty_slot_color` = มี item
2. **ไม่มี item** → รอแล้วสแกนซ้ำ (ไม่หยุด, **ไม่เปลี่ยน Stash tab**)
3. มี item → เช็กสี Stash ช่องสุดท้าย → ย้าย item ด้วย right-click
4. Stash เต็ม → เปลี่ยน tab ถัดไป (1 → 2 → 3)
5. **หยุดอัตโนมัติเฉพาะ** Stash tab 3 ช่องสุดท้ายเต็ม
6. หยุดเอง: Esc / FAILSAFE / Ctrl+C

---

## 4. วิธีหยุด

| วิธี | การทำงาน |
|------|----------|
| **Esc** | หยุดอย่างปลอดภัย |
| **FAILSAFE** | ขยับเมาส์ไปมุมซ้ายบนสุดของจอ |
| **Ctrl+C** | หยุดใน terminal |

หยุดอัตโนมัติ: **Stash tab 3 ช่องสุดท้ายเต็ม** เท่านั้น  
Hero ว่าง → บอทจะรอและสแกนซ้ำ (ไม่หยุด, ไม่คลิก Stash)

---

## 5. ปรับแต่ง / Troubleshooting

| อาการ | แก้ |
|-------|-----|
| Stash ยังไม่เต็มแต่สลับ tab | เพิ่ม `color_tolerance` ใน `config.json` (เช่น 20–25) |
| Stash เต็มแล้วแต่ไม่สลับ tab | ลด `color_tolerance` (เช่น 10–12) |
| Hero ไม่เจอ item | calibrate สีช่องว่างใหม่ / ปรับ tolerance |
| เปลี่ยน tab เร็วเกินไป | เพิ่ม `stash_tab_switch_delay_sec` (เช่น 1.0) |
| `Config error` | รัน `python calibrate.py` ใหม่ |

---

## โครงสร้างไฟล์

```
taskBarHero/
├── calibrate.py
├── bot.py
├── grid_utils.py
├── config.json
├── requirements.txt
└── howToRun.md
```

---

## Disclaimer

การใช้ automation อาจขัดกับข้อกำหนดของเกม ใช้ด้วยความเสี่ยงของตัวเอง
