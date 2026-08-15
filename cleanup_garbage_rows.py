"""
cleanup_garbage_rows.py
-------------------------
สคริปต์ลบแถวขยะที่ตกค้างจากบั๊กเก่า (แถว 1001-1008 ที่มีข้อมูลเลื่อนหลุดคอลัมน์)
ลบผ่าน Google Sheets API โดยตรง ไม่ต้องคลิกในหน้าเว็บเลย

วิธีใช้:
    วางไฟล์นี้ในโฟลเดอร์เดียวกับ sheets_client.py และ credentials.json
    แล้วรัน: py cleanup_garbage_rows.py
"""

from sheets_client import get_worksheet

START_ROW = 1001
END_ROW = 1008  # ปรับเลขนี้ถ้าจำนวนแถวขยะไม่ตรง (เช็คใน Sheet ก่อนรันถ้าไม่แน่ใจ)

def main():
    ws = get_worksheet()
    print(f"กำลังตรวจสอบแถว {START_ROW} ถึง {END_ROW} ก่อนลบ...")

    # แสดงตัวอย่างข้อมูลก่อนลบ เพื่อให้ยืนยันว่าลบถูกแถว
    sample = ws.get(f"A{START_ROW}:F{END_ROW}")
    print("ตัวอย่างข้อมูลที่จะถูกลบ (คอลัมน์ A-F):")
    for i, row in enumerate(sample):
        print(f"  แถว {START_ROW + i}: {row}")

    confirm = input(f"\nยืนยันลบแถว {START_ROW}-{END_ROW} ทั้งหมด? พิมพ์ 'yes' เพื่อยืนยัน: ")
    if confirm.strip().lower() != "yes":
        print("ยกเลิกการลบ")
        return

    ws.delete_rows(START_ROW, END_ROW)
    print(f"ลบแถว {START_ROW}-{END_ROW} สำเร็จแล้ว!")

if __name__ == "__main__":
    main()