import urllib.request, json, urllib.parse
q = urllib.parse.urlencode({'search':'Edge target zero'})
url = f'http://127.0.0.1:8000/api/records?{q}'
with urllib.request.urlopen(url, timeout=10) as r:
    data = json.load(r)
print(json.dumps(data, ensure_ascii=False, indent=2))
