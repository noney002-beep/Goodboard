import urllib.request, csv, io, json, time, shutil, os
from pathlib import Path
ROOT = Path(__file__).resolve().parent
SHEET_URL = 'https://docs.google.com/spreadsheets/d/1obXzR3E_h4O8a0vcbBV4tjo4hNvdRS2Cdq0PRKQmP6E/export?format=csv&gid=2045278866'
SHEET_USERS_URL = 'https://docs.google.com/spreadsheets/d/1obXzR3E_h4O8a0vcbBV4tjo4hNvdRS2Cdq0PRKQmP6E/export?format=csv&gid=9560291'
PROD = ROOT / 'production-data.json'
USERS = ROOT / 'users.json'

def backup(path):
    if not path.exists():
        return None
    ts = time.strftime('%Y%m%d%H%M%S')
    dest = path.with_suffix(path.suffix + f'.bak.{ts}')
    shutil.copy2(path, dest)
    return dest


def fetch_csv(url, timeout=25):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        txt = r.read().decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(txt))
    return list(reader)


def main():
    print('Backing up local files...')
    b1 = backup(PROD)
    b2 = backup(USERS)
    print('backups:', b1, b2)
    ok = False
    try:
        print('Fetching production sheet...')
        rows = fetch_csv(SHEET_URL)
        with PROD.open('w', encoding='utf-8') as fh:
            json.dump(rows, fh, ensure_ascii=False, indent=2)
        print('Wrote', PROD, 'rows=', len(rows))
        print('Fetching users sheet...')
        urows = fetch_csv(SHEET_USERS_URL)
        with USERS.open('w', encoding='utf-8') as fh:
            json.dump(urows, fh, ensure_ascii=False, indent=2)
        print('Wrote', USERS, 'rows=', len(urows))
        ok = True
    except Exception as e:
        print('ERROR fetching sheets:', e)
    if not ok:
        print('Restoring backups if any...')
        if b1 and b1.exists(): shutil.copy2(b1, PROD)
        if b2 and b2.exists(): shutil.copy2(b2, USERS)
        print('Restore done')

if __name__ == '__main__':
    main()
