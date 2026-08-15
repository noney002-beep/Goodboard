import csv
import io
import json
import mimetypes
import os
import urllib.parse
import urllib.request
import hashlib
import uuid
from datetime import datetime
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# โหลดค่าตั้งค่าจากไฟล์ .env อัตโนมัติ (ถ้ามี) เพื่อให้ค่าตั้งค่าเหมือนกัน
# ไม่ว่าจะรันด้วย python app.py ตรงๆ หรือผ่าน run_server.bat
# หมายเหตุ: จะไม่ทับค่าที่ตั้งไว้แล้วใน environment (เช่นจาก .bat หรือ Render)
def _load_dotenv(path):
    if not path.exists():
        return
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, value = line.partition('=')
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value

_load_dotenv(ROOT / '.env')

SHEET_URL = 'https://docs.google.com/spreadsheets/d/1obXzR3E_h4O8a0vcbBV4tjo4hNvdRS2Cdq0PRKQmP6E/export?format=csv&gid=2045278866'
SHEET_USERS_URL = 'https://docs.google.com/spreadsheets/d/1obXzR3E_h4O8a0vcbBV4tjo4hNvdRS2Cdq0PRKQmP6E/export?format=csv&gid=9560291'
DATA_FILE = ROOT / 'production-data.json'
USERS_FILE = ROOT / 'users.json'
APPS_SCRIPT_URL = os.environ.get('APPS_SCRIPT_URL', '').strip()
APPS_SCRIPT_TIMEOUT = int(os.environ.get('APPS_SCRIPT_TIMEOUT', '20'))

# เขียนลง Google Sheet โดยตรงผ่าน Service Account (แทนที่การพึ่งพา Apps Script)
try:
    from sheets_client import append_problem_row
    SHEETS_DIRECT_WRITE = True
except Exception as _sheets_import_error:
    append_problem_row = None
    SHEETS_DIRECT_WRITE = False
    print('SHEETS_CLIENT_IMPORT_FAILED:', _sheets_import_error)


def fetch_sheet_rows(url=SHEET_URL, allow_fallback=True):
    try:
        # Cache-buster: Google's CSV export endpoint aggressively caches
        # responses, which can cause newly-written rows (added via gspread)
        # to be invisible for several minutes. Adding a unique, changing
        # query param plus no-cache headers forces a fresh fetch every time.
        cache_buster = f"{'&' if '?' in url else '?'}_cb={int(time.time() * 1000)}"
        busted_url = url + cache_buster
        req = urllib.request.Request(
            busted_url,
            headers={
                'User-Agent': 'Mozilla/5.0',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
            },
        )
        with urllib.request.urlopen(req, timeout=25) as response:
            text = response.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        # If we have a local DATA_FILE with pending records, merge them by Row_Key
        try:
            if DATA_FILE.exists():
                with DATA_FILE.open('r', encoding='utf-8') as fh:
                    local = json.load(fh) or []
                # Build set of existing Row_Key
                keys = {str(get_record_value(r, 'Row_Key')).strip() for r in rows}
                for r in local:
                    rk = str(get_record_value(r, 'Row_Key')).strip()
                    if rk and rk not in keys:
                        rows.append(r)
        except Exception:
            pass
        return rows
    except Exception:
        if allow_fallback and DATA_FILE.exists():
            with DATA_FILE.open('r', encoding='utf-8') as fh:
                return json.load(fh)
        return []


def get_record_value(record, key):
    if key in record:
        return record[key]
    lower_key = key.lower()
    for k, v in record.items():
        if k.lower() == lower_key:
            return v
    return ''


def hash_password(password, salt):
    if password is None:
        return ''
    if salt is None:
        salt = ''
    raw = f"{password}::{salt}".encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def find_user_row(rows, username):
    if not username:
        return None
    normalized = str(username).strip().lower()
    for row in rows:
        if str(get_record_value(row, 'Username')).strip().lower() == normalized:
            return row
    return None


def login_user(username, password):
    username = str(username or '').strip()
    password = str(password or '')
    if not username or not password:
        return {'ok': False, 'msg': '⚠️ กรุณากรอก Username และ Password'}

    rows = fetch_sheet_rows(SHEET_USERS_URL, allow_fallback=False)
    if not rows:
        # Try local users.json fallback for local/offline testing
        try:
            if USERS_FILE.exists():
                with USERS_FILE.open('r', encoding='utf-8') as fh:
                    local_users = json.load(fh) or []
                # Expecting a list of user dicts similar to sheet rows
                rows = local_users
        except Exception:
            rows = []
    if not rows:
        return {'ok': False, 'msg': '❌ ไม่สามารถเชื่อมข้อมูลผู้ใช้ได้ หรือไม่มีข้อมูลผู้ใช้ใน sheet/ไฟล์ท้องถิ่น'}

    user = find_user_row(rows, username)
    if not user:
        return {'ok': False, 'msg': '❌ ไม่พบบัญชีผู้ใช้นี้'}
    password_hash = str(get_record_value(user, 'Password_Hash') or '').strip()
    salt = str(get_record_value(user, 'Salt') or '').strip()
    plain_password = str(get_record_value(user, 'Password') or '').strip()

    if password_hash:
        if hash_password(password, salt) != password_hash:
            return {'ok': False, 'msg': '❌ Password ไม่ถูกต้อง'}
    elif plain_password:
        if password != plain_password:
            return {'ok': False, 'msg': '❌ Password ไม่ถูกต้อง'}
    else:
        return {'ok': False, 'msg': '❌ ไม่พบรหัสผ่านในข้อมูลผู้ใช้'}

    return {
        'ok': True,
        'msg': '✅ เข้าสู่ระบบสำเร็จ',
        'user': {
            'Emp_ID': str(get_record_value(user, 'Emp_ID') or '').strip(),
            'First_Name': str(get_record_value(user, 'First_Name') or '').strip(),
            'Last_Name': str(get_record_value(user, 'Last_Name') or '').strip(),
            'Full_Name': ('{0} {1}'.format(str(get_record_value(user, 'First_Name') or '').strip(), str(get_record_value(user, 'Last_Name') or '').strip())).strip(),
            'Username': str(get_record_value(user, 'Username') or '').strip(),
            'Role': str(get_record_value(user, 'Role') or 'User').strip(),
            'Kumi': str(get_record_value(user, 'Kumi') or '').strip(),
            'Shift': str(get_record_value(user, 'Shift') or '').strip(),
        }
    }


def filter_records(rows, filters):
    if not filters:
        return rows
    def matches(row):
        if 'kpi' in filters:
            values = filters['kpi']
            if isinstance(values, str):
                values = [values] if values.strip() else []
            values = [str(v).strip() for v in (values or []) if str(v).strip()]
            if values:
                raw = str(
                    get_record_value(row, 'KPI') or
                    get_record_value(row, 'kpi') or
                    get_record_value(row, 'KPI Name') or
                    get_record_value(row, 'kpi_name') or
                    ''
                )
                if not any(raw.strip().lower() == v.lower() for v in values):
                    return False
        if 'shift' in filters:
            desired = str(filters['shift']).strip().lower()
            actual = str(
                get_record_value(row, 'Problem_Shift') or
                get_record_value(row, 'shift') or
                get_record_value(row, 'Shift') or
                ''
            ).strip().lower()
            if desired and actual != desired:
                return False
        if 'search' in filters:
            query = str(filters['search'] or '').strip().lower()
            if query:
                hay = ' '.join([
                    str(get_record_value(row, 'Kumi') or ''),
                    str(get_record_value(row, 'Detail') or ''),
                    str(get_record_value(row, 'Full_Name') or ''),
                    str(get_record_value(row, 'Problem_Actual') or ''),
                    str(get_record_value(row, 'Problem_Target') or ''),
                    str(get_record_value(row, 'Main_KPI') or ''),
                    str(get_record_value(row, 'Sub_KPI') or ''),
                    str(get_record_value(row, 'Process_KPI') or ''),
                ]).lower()
                if query not in hay:
                    return False
        return True
    return [row for row in rows if matches(row)]


def sort_records(rows, sort_col, sort_dir):
    if not sort_col:
        return rows
    def sort_key(row):
        value = get_record_value(row, sort_col)
        if isinstance(value, str):
            return value.strip().lower()
        return value
    reverse = sort_dir.lower() == 'desc'
    try:
        return sorted(rows, key=sort_key, reverse=reverse)
    except Exception:
        return rows


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, payload, status=200):
        body = json.dumps(payload).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        # Server-Sent Events stream for real-time updates
        if parsed.path == '/api/stream':
            try:
                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream')
                self.send_header('Cache-Control', 'no-cache')
                self.send_header('Connection', 'keep-alive')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()

                last_hash = None
                while True:
                    try:
                        rows = fetch_sheet_rows()
                        payload = {'records': rows, 'pages': 1, 'total': len(rows), 'source': 'sheet'}
                        s = json.dumps(payload, ensure_ascii=False)
                        h = hashlib.sha256(s.encode('utf-8')).hexdigest()
                        if h != last_hash:
                            msg = 'data: ' + s + '\n\n'
                            self.wfile.write(msg.encode('utf-8'))
                            self.wfile.flush()
                            last_hash = h
                        # heartbeat comment to keep connection alive
                        self.wfile.write(b':\n\n')
                        self.wfile.flush()
                    except BrokenPipeError:
                        break
                    except Exception:
                        # on any error, wait then retry
                        try:
                            time.sleep(5)
                        except Exception:
                            break
                    time.sleep(5)
            except Exception:
                pass
            return

        # continue with normal GET handling
        if parsed.path == '/api/production-data':
            try:
                rows = fetch_sheet_rows()
                filtered = [
                    row for row in rows
                    if str(row.get('KPI') or '').strip().lower() in {'production', 'prod', 'productions'}
                ]
                self._send_json({'records': filtered, 'pages': 1, 'total': len(filtered)})
            except Exception as exc:
                self._send_json({'ok': False, 'error': str(exc)}, 500)
            return

        if parsed.path == '/api/records':
            try:
                rows = fetch_sheet_rows()
                query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
                filters = {}
                if 'kpi' in query:
                    filters['kpi'] = [v for v in query.get('kpi', []) if v.strip() != '']
                if 'shift' in query:
                    filters['shift'] = query.get('shift', [''])[0]
                if 'search' in query:
                    filters['search'] = query.get('search', [''])[0]
                history_mode = 'history' in query and query.get('history', ['0'])[0] != '0'
                detail_key = query.get('detail', [''])[0]

                if detail_key:
                    rows = [row for row in rows if str(get_record_value(row, 'Row_Key')).strip() == detail_key]
                    return self._send_json({'record': rows[0] if rows else None})

                sort_col = query.get('sort_col', [''])[0] if 'sort_col' in query else ''
                sort_dir = query.get('sort_dir', ['asc'])[0] if 'sort_dir' in query else 'asc'
                page = int(query.get('page', ['1'])[0] or 1)
                per_page = int(query.get('per_page', ['200'])[0] or 200)

                rows = filter_records(rows, filters)
                rows = sort_records(rows, sort_col, sort_dir)

                total = len(rows)
                pages = max(1, (total + per_page - 1) // per_page)
                start = (page - 1) * per_page
                page_rows = rows[start:start + per_page]

                payload = {'records': page_rows, 'pages': pages, 'total': total}
                if history_mode:
                    stats = {}
                    for row in rows:
                        label = str(get_record_value(row, 'KPI') or get_record_value(row, 'kpi') or get_record_value(row, 'KPI Name') or get_record_value(row, 'kpi_name') or '').strip() or 'Unknown'
                        stats[label] = stats.get(label, 0) + 1
                    payload['stats'] = [{'kpi': k, 'cnt': v} for k, v in stats.items()];
                    payload['page'] = page
                self._send_json(payload)
            except Exception as exc:
                self._send_json({'ok': False, 'error': str(exc)}, 500)
            return

        path = parsed.path
        if path in ('', '/', '/index.html'):
            self.send_response(302)
            self.send_header('Location', '/login.html')
            self.end_headers()
            return
        file_path = (ROOT / path.lstrip('/')).resolve()
        if not str(file_path).startswith(str(ROOT)):
            self.send_error(403)
            return
        if file_path.is_dir():
            file_path = file_path / 'index.html'
        if not file_path.exists():
            self.send_error(404)
            return
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type is None:
            mime_type = 'application/octet-stream'
        body = file_path.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', mime_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path not in ('/api', '/api/', '/api/login', '/login'):
            self.send_error(404)
            return

        content_length = int(self.headers.get('Content-Length', '0'))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ''
        try:
            data = json.loads(body)
        except Exception as exc:
            return self._send_json({'ok': False, 'msg': 'Invalid JSON: ' + str(exc)}, 400)

        action = data.get('action')
        args = data.get('args', [])
        if action == 'loginUser':
            username = args[0] if len(args) > 0 else ''
            password = args[1] if len(args) > 1 else ''
            result = login_user(username, password)
            return self._send_json(result)

        if action == 'submitRecord':
            payload = args[0] if len(args) > 0 else {}
            # minimal validation
            if not isinstance(payload, dict):
                return self._send_json({'ok': False, 'msg': 'Invalid payload'}, 400)

            # ensure Row_Key
            row_key = payload.get('Row_Key') or str(uuid.uuid4())
            payload['Row_Key'] = row_key
            # add created_at if missing
            if not payload.get('created_at'):
                payload['created_at'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

            # append to local DATA_FILE
            try:
                local = []
                if DATA_FILE.exists():
                    with DATA_FILE.open('r', encoding='utf-8') as fh:
                        local = json.load(fh) or []
                local.append(payload)
                with DATA_FILE.open('w', encoding='utf-8') as fh:
                    json.dump(local, fh, ensure_ascii=False, indent=2)
            except Exception as exc:
                return self._send_json({'ok': False, 'msg': 'Failed saving local data: ' + str(exc)}, 500)

            sync_msg = None
            if SHEETS_DIRECT_WRITE:
                # วิธีใหม่: เขียนลง Google Sheet ตรงๆ ผ่าน Service Account (gspread)
                try:
                    append_problem_row(payload)
                    sync_msg = ' และบันทึกลง Google Sheet สำเร็จ'
                    print('SHEET_DIRECT_WRITE OK: row_key=', row_key)
                except Exception as exc:
                    sync_msg = ' แต่บันทึกลง Google Sheet ไม่สำเร็จ: ' + str(exc)
                    print('SHEET_DIRECT_WRITE_ERROR:', str(exc))
            elif APPS_SCRIPT_URL:
                # วิธีเดิม (fallback): ส่งผ่าน Google Apps Script webhook
                try:
                    sync_payload = json.dumps({'action': 'submitRecord', 'args': [payload]}).encode('utf-8')
                    req = urllib.request.Request(
                        APPS_SCRIPT_URL,
                        data=sync_payload,
                        headers={'Content-Type': 'application/json;charset=utf-8'}
                    )
                    with urllib.request.urlopen(req, timeout=APPS_SCRIPT_TIMEOUT) as resp:
                        text = resp.read().decode('utf-8')
                    try:
                        sync_result = json.loads(text)
                        if not sync_result.get('ok'):
                            sync_msg = ' แต่ไม่สามารถซิงค์ขึ้น Sheet ได้: ' + str(sync_result.get('msg') or 'unknown')
                            print('APPS_SCRIPT_SYNC FAILED:', APPS_SCRIPT_URL, 'response=', text)
                        else:
                            sync_msg = ' และซิงค์ขึ้น Sheet สำเร็จ'
                            print('APPS_SCRIPT_SYNC OK:', APPS_SCRIPT_URL, 'response=', text)
                    except Exception as exc:
                        sync_msg = ' แต่ได้รับการตอบกลับจาก Sheet ที่ไม่ถูกต้อง'
                        print('APPS_SCRIPT_SYNC PARSE ERROR:', APPS_SCRIPT_URL, 'text=', text, 'error=', exc)
                except Exception as exc:
                    sync_msg = ' แต่ไม่สามารถซิงค์ขึ้น Sheet ได้: ' + str(exc)
                    print('APPS_SCRIPT_SYNC ERROR:', APPS_SCRIPT_URL, str(exc))
            else:
                sync_msg = ' (ยังไม่ได้ตั้งค่าการเชื่อมต่อ Google Sheet ใดๆ - ตรวจสอบว่ามีไฟล์ credentials.json หรือ GOOGLE_SERVICE_ACCOUNT_JSON)'
                print('SHEET_SYNC_SKIPPED: no direct-write client and no APPS_SCRIPT_URL configured')

            msg = '✅ บันทึกสำเร็จ'
            if sync_msg:
                msg += sync_msg
            return self._send_json({'ok': True, 'msg': msg, 'row_key': row_key, 'record': payload})

        if action == 'getHistoryRecords':
            filters = args[0] if len(args) > 0 and isinstance(args[0], dict) else {}
            try:
                rows = fetch_sheet_rows()
                rows = filter_records(rows, filters)
                sort_col = str(filters.get('sort_col') or 'record_date')
                sort_dir = str(filters.get('sort_dir') or 'desc')
                rows = sort_records(rows, sort_col, sort_dir)
                total = len(rows)
                per_page = int(filters.get('per_page') or 8)
                page = int(filters.get('page') or 1)
                page = max(1, page)
                pages = max(1, (total + per_page - 1) // per_page)
                start = (page - 1) * per_page
                page_rows = rows[start:start + per_page]
                stats = {}
                for row in rows:
                    kpi = str(get_record_value(row, 'KPI') or get_record_value(row, 'kpi') or '').strip() or 'Unknown'
                    stats[kpi] = stats.get(kpi, 0) + 1
                payload = {
                    'records': page_rows,
                    'pages': pages,
                    'page': page,
                    'total': total,
                    'stats': [{'kpi': k, 'cnt': v} for k, v in stats.items()]
                }
                return self._send_json(payload)
            except Exception as exc:
                return self._send_json({'ok': False, 'msg': 'Failed loading history: ' + str(exc)}, 500)

        if action == 'getRecordDetail':
            row_key = args[0] if len(args) > 0 else ''
            try:
                rows = fetch_sheet_rows()
                record = None
                for row in rows:
                    if str(get_record_value(row, 'Row_Key')).strip() == str(row_key).strip():
                        record = row
                        break
                return self._send_json({'record': record})
            except Exception as exc:
                return self._send_json({'ok': False, 'msg': 'Failed loading record detail: ' + str(exc)}, 500)

        return self._send_json({'ok': False, 'msg': 'Unknown action: ' + str(action)}, 400)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', '8001'))
    print(f'Starting server on port {port} (set PORT env var or .env to change)')
    server = ThreadingHTTPServer(('0.0.0.0', port), Handler)
    # Get local IP address for display
    import socket
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
    except:
        local_ip = 'localhost'
    print(f'Serving on http://0.0.0.0:{port}')
    print(f'Access from this computer: http://127.0.0.1:{port}')
    print(f'Access from other devices: http://{local_ip}:{port}')
    server.serve_forever()