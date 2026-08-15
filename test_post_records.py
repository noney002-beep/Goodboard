import urllib.request, json
url='http://127.0.0.1:8000/api'
records=[
  {"KPI":"Environment","Main_KPI":"Co2 and Energy","Sub_KPI":"Energy","Problem_Target":"0","Problem_Actual":"5","Problem_Shift":"White","Kumi":"Test","Detail":"Edge target zero"},
  {"KPI":"Environment","Main_KPI":"Waste","Sub_KPI":"Waste","Problem_Actual":"3","Problem_Shift":"White","Kumi":"Test","Detail":"Missing target"},
  {"KPI":"Environment","Main_KPI":"Water","Sub_KPI":"Water","Problem_Target":"10","Problem_Actual":"6","Problem_Shift":"White","Kumi":"Test","Detail":"Actual less than target"}
]
for i,p in enumerate(records,1):
    data={'action':'submitRecord','args':[p]}
    req=urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            resp=r.read().decode('utf-8')
    except Exception as e:
        resp=str(e)
    print(f'RECORD {i} RESPONSE:')
    print(resp)
