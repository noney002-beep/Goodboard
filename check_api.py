import urllib.request
import sys
try:
    data = urllib.request.urlopen('http://127.0.0.1:8001/api/records').read().decode('utf-8')
    print(data)
except Exception as e:
    print('ERROR', e)
    sys.exit(1)
