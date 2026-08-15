# 📱 คู่มือการใช้งาน KPI Monitoring บนมือถือและ PC

## 🚀 เริ่มต้นการใช้งาน

### 1️⃣ เปิดเซิร์ฟเวอร์

รันคำสั่งนี้ใน PowerShell:
```powershell
cd c:\Users\USER\Desktop\testphone
python app.py
```

ผลลัพธ์จะแสดง:
```
Serving on http://0.0.0.0:8000
Access from this computer: http://127.0.0.1:8000
Access from other devices: http://YOUR.IP.ADDRESS:8000
```

---

## 💻 เข้าถึงจาก PC

**URL:** `http://127.0.0.1:8000`

หรือ **URL อื่น:**
- `http://localhost:8000`
- `http://YOUR.IP.ADDRESS:8000`

---

## 📱 เข้าถึงจากโทรศัพท์มือถือ

### วิธีหา IP Address ของเครื่อง PC

**วิธี 1: ดู Terminal/PowerShell**
เมื่อรันคำสั่ง `python app.py` จะได้บรรทัด:
```
Access from other devices: http://192.168.x.x:8000
```
ใช้ IP Address นั้นเลย

**วิธี 2: หา IP ด้วย Command**
```powershell
ipconfig
```
หา IPv4 Address (จะเห็นประมาณ `192.168.x.x` หรือ `10.0.x.x`)

---

### ขั้นตอนการเข้าถึงจากมือถือ

1. **ต่อ WiFi เดียวกันกับ PC**
   - ต้องอยู่บนเครือข่ายเดียวกันเท่านั้น

2. **เปิด Browser (Chrome, Safari, Firefox ฯลฯ)**

3. **พิมพ์ URL:**
   ```
   http://192.168.x.x:8000
   ```
   (แทนที่ `192.168.x.x` ด้วย IP Address จริงของคุณ)

4. **กด Enter**
   - หน้า Login จะขึ้นมา

---

## 🔐 เข้าสู่ระบบ

ใช้ข้อมูลผู้ใช้:
- **Username:** ตัวอักษรในแฟ้ม `users.json`
- **Password:** ตัวอักษรในแฟ้ม `users.json`

หรือใช้ข้อมูลทดสอบ:
- **Username:** `testuser`
- **Password:** `password`

---

## 📊 หน้าหลัก (Menu)

หลังจากเข้าสู่ระบบจะเห็น 6 เรื่อง KPI:
1. **Safety** - ความปลอดภัย
2. **Environment** - สิ่งแวดล้อม
3. **Quality** - คุณภาพ
4. **Production** - การผลิต
5. **Cost** - ต้นทุน
6. **HRD** - ทรัพยากรบุคคล

---

## 📝 บันทึกปัญหา (Form)

1. กดปุ่ม "บันทึกปัญหา" หรือเข้า `/form.html`
2. ระบบจะเติมข้อมูล:
   - รหัสพนักงาน (อัตโนมัติ)
   - หน่วยงาน (Kumi) ถูกล็อก
   - กะงาน (Shift) ถูกล็อก

3. เลือกข้อมูล:
   - **KPI:** Safety, Environment, Quality, etc.
   - **Main KPI:** เลือกเมื่อเลือก KPI เสร็จ
   - **Sub KPI:** เลือกเมื่อเลือก Main KPI เสร็จ
   - **Process KPI:** เลือกเมื่อเลือก Sub KPI เสร็จ

4. ระบบจะเติมหน่วย (Unit) อัตโนมัติ

5. ระบุรายละเอียดปัญหา

6. กดปุ่ม "บันทึก"

---

## 📱 โปรแกรมนี้ใช้ได้บน:

✅ **PC/Laptop**
- Windows
- macOS
- Linux

✅ **โทรศัพท์มือถือ**
- iPhone/iPad (Safari)
- Android (Chrome, Firefox)

✅ **Tablet**
- ทุกระบบ

---

## 🔧 แก้ไขปัญหา

### ❌ "ไม่สามารถเข้าถึงได้" จากมือถือ

**สาเหตุ:**
- ไม่ได้ต่อ WiFi เดียวกันกับ PC
- IP Address ไม่ถูกต้อง
- Firewall ปิดกั้น

**วิธีแก้:**
1. ตรวจสอบ WiFi เหมือนกันหรือไม่
2. ดู Terminal ขณะรัน `python app.py` เพื่อหา IP ที่ถูกต้อง
3. ปิด Firewall ชั่วคราวหรือให้ Port 8000 ผ่าน

### ❌ "Server ไม่พบ"

**วิธีแก้:**
1. ตรวจสอบว่า `python app.py` ยังทำงานอยู่
2. พยายามเข้า `http://127.0.0.1:8000` จาก PC ลองดู
3. ตรวจสอบ Port 8000 ว่าว่างอยู่หรือไม่

---

## 💡 เคล็ดลับใช้งาน

✨ **ทั้ง PC และมือถือใช้ URL เดียวกัน:**
```
http://192.168.x.x:8000
```

✨ **บันทึกในสมุดบันทึก:**
- เขียน IP Address ของคุณไว้:
  ```
  http://192.168.___.___:8000
  ```
- แบ่งให้ผู้ที่ต้องการใช้

✨ **ใช้ได้ Offline หลังจากดาวน์โหลด:**
- เซิร์ฟเวอร์บันทึกข้อมูลในไฟล์ JSON ท้องถิ่น
- จะเชื่อมต่อกับ Google Sheet เมื่อมี WiFi

---

## 📞 การติดต่อ

หากมีปัญหา:
1. ตรวจสอบ Terminal ว่ามี Error ไหม
2. ดู Browser Console (F12) หากมี Error ไหม
3. ลองรีสตาร์ท Server (`python app.py` อีกครั้ง)

---

**อัปเดต:** 2026-08-04
**เวอร์ชัน:** 1.0 Mobile Optimized
