import urllib.request, json
payload = {
    'action': 'submitRecord',
    'args': [
        {
            'Emp_ID': '999',
            'Full_Name': 'Test User',
            'KPI': 'Environment',
            'Main_KPI': 'Co2 and Energy',
            'Sub_KPI': 'Test',
            'Problem_Date': '2026-08-04',
            'Problem_Target': '10',
            'Problem_Actual': '12',
            'record_date': '2026-08-04'
        }
    ]
}
req = urllib.request.Request('http://127.0.0.1:8000/api', data=json.dumps(payload).encode('utf-8'), headers={'Content-Type':'application/json'})
resp = urllib.request.urlopen(req)
print(resp.read().decode('utf-8'))
