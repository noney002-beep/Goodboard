"""
diagnose_rows.py
------------------
สคริปต์ตรวจสอบข้อมูลดิบในชีต เพื่อหาสาเหตุว่าทำไมระบบคำนวณแถวว่างผิดพลาด
รันด้วย: py diagnose_rows.py
"""

from sheets_client import get_worksheet, COLUMNS

ws = get_worksheet()
all_values = ws.get_all_values()

print(f"จำนวนแถวทั้งหมดที่ดึงมาได้ (รวม header): {len(all_values)}")
print(f"Header (แถว 1): {all_values[0]}")
print()
print("=== ตรวจสอบแถว 68-80 (index 67-79) แบบดิบๆ ===")
for i in range(67, min(80, len(all_values))):
    row = all_values[i]
    row_num = i + 1
    non_empty = [(COLUMNS[j] if j < len(COLUMNS) else f"col{j}", val)
                 for j, val in enumerate(row) if val.strip()]
    print(f"แถว {row_num}: {non_empty if non_empty else '(ว่างเปล่าสนิท)'}")

print()
print("=== ตรวจสอบแถว 1000-1007 (ท้ายสุดของชีต) ===")
for i in range(999, min(1007, len(all_values))):
    row = all_values[i]
    row_num = i + 1
    non_empty = [(COLUMNS[j] if j < len(COLUMNS) else f"col{j}", val)
                 for j, val in enumerate(row) if val.strip()]
    print(f"แถว {row_num}: {non_empty if non_empty else '(ว่างเปล่าสนิท)'}")