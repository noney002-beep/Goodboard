"""
sheets_client.py
-----------------
โมดูลเชื่อมต่อ Google Sheet "GL_Board" แทนการ sync เข้า SQL/PostgreSQL
ใช้ไลบรารี gspread + google-auth (Service Account)

การติดตั้ง:
    pip install gspread google-auth

การตั้งค่า:
    1. เก็บไฟล์ credentials.json (Service Account key) ไว้ในโฟลเดอร์โปรเจกต์
       (หรืออ่านจาก Environment Variable ตามคำแนะนำด้านล่าง)
    2. ตั้งค่า SPREADSHEET_ID และ WORKSHEET_NAME ให้ตรงกับของจริง
"""

import os
import json
import uuid
import base64
import io as _io
from datetime import datetime
from functools import lru_cache

import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

# ID ของ Google Sheet (คัดลอกมาจาก URL ระหว่าง /d/ กับ /edit)
SPREADSHEET_ID = "1obXzR3E_h4O8a0vcbBV4tjo4hNvdRS2Cdq0PRKQmP6E"

# ชื่อแท็บ (tab) ที่เก็บข้อมูลหลัก - จากที่เห็นมีแท็บ Sheet1 / Users_Login / GLBoard
# ปรับชื่อให้ตรงกับแท็บจริงที่เก็บข้อมูล KPI/Problem
WORKSHEET_NAME = "GLBoard"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

# คอลัมน์ตามลำดับจริงในชีต (แถวที่ 1 ของ GL_Board) - ยืนยันจากภาพหน้าจอจริง
# มี 25 คอลัมน์ (A ถึง Y) ไม่มีคอลัมน์ Role_User
COLUMNS = [
    "ID", "Emp_ID", "Problem_Date", "record_date", "Kumi", "KPI",
    "Problem_Shift", "Process_KPI", "Main_KPI", "Sub_KPI", "Problem_Hour",
    "Problem_Actual", "Problem_Target", "Problem_QTY", "QTY_Unit",
    "Unit_Problem", "Problem_Time", "Detail", "Countermeasure",
    "Image_Name", "created_at", "Full_Name", "Row_Key",
    "SQL_Synced", "Sync_Note", "Image_URL",
]

# (ไม่บังคับ) ใส่ Folder ID ของ Google Drive ที่ต้องการเก็บรูป โดยแชร์สิทธิ์ Editor
# ให้กับอีเมลของ Service Account ไว้ก่อน ถ้าปล่อยว่างจะอัปโหลดไปที่ "My Drive"
# ของ Service Account เอง (ยังใช้งานได้ปกติ เพียงแต่จัดระเบียบยากกว่า)
DRIVE_FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID", "").strip()


def _load_credentials() -> Credentials:
    """
    โหลด credentials จาก 2 ทางเลือก:
    1) Environment Variable GOOGLE_SERVICE_ACCOUNT_JSON (แนะนำสำหรับ deploy บน Render)
       -> ใส่เนื้อหาไฟล์ .json ทั้งหมดเป็น string ใน env var นี้
    2) ไฟล์ credentials.json ในโฟลเดอร์เดียวกับสคริปต์นี้ (ใช้ตอน dev บนเครื่อง)
    """
    env_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if env_json:
        info = json.loads(env_json)
        return Credentials.from_service_account_info(info, scopes=SCOPES)

    cred_path = os.path.join(os.path.dirname(__file__), "credentials.json")
    if not os.path.exists(cred_path):
        raise FileNotFoundError(
            "ไม่พบ credentials.json และไม่มี GOOGLE_SERVICE_ACCOUNT_JSON "
            "ใน environment variable กรุณาตั้งค่าอย่างใดอย่างหนึ่ง"
        )
    return Credentials.from_service_account_file(cred_path, scopes=SCOPES)


@lru_cache(maxsize=1)
def get_worksheet():
    """คืนค่า worksheet object (cache ไว้ ไม่ต้อง auth ใหม่ทุกครั้ง)"""
    creds = _load_credentials()
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID)
    return sheet.worksheet(WORKSHEET_NAME)


@lru_cache(maxsize=1)
def get_drive_service():
    """คืนค่า Google Drive API client (ใช้ Service Account เดียวกับ Sheet)"""
    creds = _load_credentials()
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def upload_image_to_drive(base64_data: str, mime_type: str = None, filename: str = None) -> str:
    """
    อัปโหลดรูปภาพ (Base64) ขึ้น Google Drive แล้วเปิดสิทธิ์ให้ "ทุกคนที่มีลิงก์" ดูรูปได้
    คืนค่าลิงก์รูปที่ใช้แสดงผลได้ตรงๆ ผ่าน <img src="...">
    ถ้าไม่มีข้อมูลรูป (base64_data ว่าง) จะคืนค่า string ว่าง
    """
    if not base64_data:
        return ""

    service = get_drive_service()
    file_bytes = base64.b64decode(base64_data)
    media = MediaIoBaseUpload(
        _io.BytesIO(file_bytes),
        mimetype=mime_type or "image/jpeg",
        resumable=False,
    )
    file_metadata = {"name": filename or f"problem_{uuid.uuid4().hex}.jpg"}
    if DRIVE_FOLDER_ID:
        file_metadata["parents"] = [DRIVE_FOLDER_ID]

    uploaded = service.files().create(
        body=file_metadata, media_body=media, fields="id"
    ).execute()
    file_id = uploaded.get("id")

    # เปิดสิทธิ์ให้ "ทุกคนที่มีลิงก์" ดูรูปได้ (จำเป็นเพื่อให้ <img> ในเว็บ/Sheet แสดงผลได้)
    service.permissions().create(
        fileId=file_id, body={"role": "reader", "type": "anyone"}
    ).execute()

    return f"https://drive.google.com/uc?export=view&id={file_id}"


def _next_empty_row(ws) -> int:
    """
    หาแถวว่างถัดไปที่แท้จริง โดยสแกนจากด้านล่างขึ้นบนหาแถวที่มี "ข้อมูลเนื้อหาจริง"
    เช็คเฉพาะคอลัมน์ที่เป็นข้อมูลกรอกจริงเท่านั้น (Kumi, Detail, Countermeasure)
    ไม่เช็คคอลัมน์อย่าง SQL_Synced/Sync_Note ที่อาจมี dropdown เติมค่าเริ่มต้น
    ไว้ล่วงหน้าหลายร้อยแถว (เช่น "FALSE" หรือ "⏳ รอ sync") ซึ่งทำให้เข้าใจผิดว่า
    แถวนั้นมีข้อมูลจริงทั้งที่ยังไม่มีใครกรอกอะไรเลย
    """
    all_values = ws.get_all_values()
    check_cols = [c for c in ("Kumi", "Detail", "Countermeasure") if c in COLUMNS]
    check_indices = [COLUMNS.index(c) for c in check_cols]

    for i in range(len(all_values) - 1, 0, -1):  # ไล่จากล่างขึ้นบน ข้าม header (index 0)
        row = all_values[i]
        has_real_data = any(
            (row[idx].strip() if idx < len(row) else "")
            for idx in check_indices
        )
        if has_real_data:
            return i + 2  # i เป็น 0-indexed, +1 แปลงเป็นเลขแถว, +1 อีกทีเพื่อไปแถวถัดไป
    return 2  # ไม่มีข้อมูลเลย เริ่มที่แถว 2 (แถวแรกหลัง header)


def append_problem_row(data: dict) -> str:
    """
    เพิ่มแถวใหม่ลงชีต (แทนการ INSERT เข้า SQL)

    data: dict ที่มี key ตรงกับ COLUMNS (ไม่ต้องครบทุกตัว ที่ขาดจะเว้นว่าง)
    คืนค่า Row_Key ที่ใช้อ้างอิงแถวนี้
    """
    ws = get_worksheet()

    row_key = data.get("Row_Key") or str(uuid.uuid4())
    created_at = data.get("created_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    record_date = data.get("record_date") or datetime.now().strftime("%Y-%m-%d")

    row_data = {**data, "Row_Key": row_key, "created_at": created_at, "record_date": record_date}

    # อัปโหลดรูปภาพขึ้น Google Drive ถ้ามีแนบมา (ฟอร์มส่ง Image_Base64 มา แต่คอลัมน์นี้
    # ไม่มีใน Sheet โดยตรง เพราะ Base64 ยาวเกินขีดจำกัดของ 1 cell ได้ง่าย
    # จึงอัปโหลดขึ้น Drive แล้วเก็บแค่ลิงก์ไว้ในคอลัมน์ Image_URL แทน)
    image_base64 = row_data.pop("Image_Base64", None)
    image_mime = row_data.pop("Image_MimeType", None)
    image_filename = row_data.pop("Image_FileName", None) or row_data.get("Image_Name")
    if image_base64:
        try:
            image_url = upload_image_to_drive(image_base64, image_mime, image_filename)
            row_data["Image_URL"] = image_url
            row_data["Image_Name"] = image_filename or row_data.get("Image_Name", "")
        except Exception as exc:
            row_data["Image_URL"] = ""
            print("DRIVE_UPLOAD_ERROR:", exc)

    # ตั้งค่า default สำหรับสถานะ sync (ไม่ต้องพึ่ง SQL อีกต่อไป
    # แต่คงคอลัมน์ไว้เผื่อยังมีระบบอื่นอ่านค่านี้อยู่)
    row_data.setdefault("SQL_Synced", "TRUE")
    row_data.setdefault("Sync_Note", "✅ direct to sheet")

    ordered_row = [row_data.get(col, "") for col in COLUMNS]

    next_row = _next_empty_row(ws)

    # ป้องกัน error "exceeds grid limits" ถ้าตำแหน่งที่จะเขียนเกินจำนวนแถวปัจจุบันของชีต
    if next_row > ws.row_count:
        ws.add_rows(next_row - ws.row_count + 10)  # เผื่อพื้นที่เพิ่มอีก 10 แถว

    end_col_letter = chr(ord('A') + len(COLUMNS) - 1)  # COLUMNS มี 25 ตัว -> Y (ไม่เกิน Z จึงไม่ต้องคิดตัวอักษรคู่)
    cell_range = f"A{next_row}:{end_col_letter}{next_row}"
    ws.update(cell_range, [ordered_row], value_input_option="USER_ENTERED")
    return row_key


def get_all_problems() -> list[dict]:
    """อ่านข้อมูลทั้งหมดจากชีต คืนค่าเป็น list ของ dict (แทนการ SELECT * จาก SQL)"""
    ws = get_worksheet()
    return ws.get_all_records()


def find_row_by_key(row_key: str) -> tuple[int, dict] | None:
    """หาแถวจาก Row_Key คืนค่า (เลขแถวในชีต, ข้อมูลแถว) หรือ None ถ้าไม่เจอ"""
    ws = get_worksheet()
    records = ws.get_all_records()
    for idx, record in enumerate(records, start=2):  # แถว 1 คือ header
        if record.get("Row_Key") == row_key:
            return idx, record
    return None


def update_row_by_key(row_key: str, updates: dict) -> bool:
    """อัปเดตข้อมูลบางฟิลด์ของแถวที่มี Row_Key ตรงกัน"""
    ws = get_worksheet()
    found = find_row_by_key(row_key)
    if not found:
        return False
    row_idx, _ = found
    for field, value in updates.items():
        if field in COLUMNS:
            col_idx = COLUMNS.index(field) + 1  # gspread นับคอลัมน์เริ่มที่ 1
            ws.update_cell(row_idx, col_idx, value)
    return True


if __name__ == "__main__":
    # ทดสอบการเชื่อมต่อแบบง่าย: อ่านข้อมูล 3 แถวแรก
    try:
        rows = get_all_problems()
        print(f"เชื่อมต่อสำเร็จ พบข้อมูลทั้งหมด {len(rows)} แถว")
        for r in rows[:3]:
            print(r)
    except Exception as e:
        print(f"เชื่อมต่อไม่สำเร็จ: {e}")