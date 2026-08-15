import json
with open('production-data.json', encoding='utf-8') as f:
    data = json.load(f)
matches = [r for r in data if 'co2' in str(r.get('Main_KPI','')).lower() or 'energy' in str(r.get('Main_KPI','')).lower() or str(r.get('KPI','')).lower()=='environment']
print('production-data.json length', len(data))
print('matches', len(matches))
for r in matches[-5:]:
    print(r.get('Row_Key'), r.get('KPI'), r.get('Main_KPI'), r.get('created_at'))
