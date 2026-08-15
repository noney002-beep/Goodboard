import urllib.request, json
resp = urllib.request.urlopen('http://127.0.0.1:8000/api/records?page=1&per_page=500').read().decode('utf-8')
obj = json.loads(resp)
matches = []
for r in obj.get('records', []):
    mk = str(r.get('Main_KPI') or '')
    kpi = str(r.get('KPI') or '')
    if 'co2' in mk.lower() or 'energy' in mk.lower() or kpi.lower() == 'environment':
        matches.append(r)
print('found count', len(matches))
for m in matches[:10]:
    print(m.get('Row_Key'), m.get('KPI'), m.get('Main_KPI'), m.get('record_date'))
print('total records returned', len(obj.get('records', [])))
