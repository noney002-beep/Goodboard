import traceback
try:
    import sheets_client
    print("IMPORT สำเร็จ! sheets_client ใช้งานได้ปกติ")
except Exception:
    print("IMPORT ล้มเหลว รายละเอียด error เต็มๆ ด้านล่าง:")
    traceback.print_exc()