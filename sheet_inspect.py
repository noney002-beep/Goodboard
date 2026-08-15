import urllib.request
import csv
import io

url = 'https://docs.google.com/spreadsheets/d/1obXzR3E_h4O8a0vcbBV4tjo4hNvdRS2Cdq0PRKQmP6E/export?format=csv&gid=2045278866'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
text = urllib.request.urlopen(req, timeout=20).read().decode('utf-8-sig')
reader = csv.DictReader(io.StringIO(text))
rows = list(reader)
env = [r for r in rows if (r.get('KPI') or '').strip().lower() == 'environment']
print('rows=', len(rows))
print('env rows=', len(env))
if rows:
    print('keys=', list(rows[0].keys()))
print('sample env rows:')
for r in env[:10]:
    print({k: r.get(k, '') for k in ['KPI', 'Main_KPI', 'Sub_KPI', 'Process_KPI', 'Problem_Date', 'record_date', 'Kumi', 'Problem_Actual', 'Problem_Target', 'Problem_Time']})
