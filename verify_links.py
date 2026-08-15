import urllib.request
import re
pages = ['Enviroment.html','Wproduction.html','Quality.html','hrd.html','safety.html','cost.html']
for p in pages:
    url = 'http://127.0.0.1:8000/' + p
    try:
        r = urllib.request.urlopen(url, timeout=5)
        html = r.read().decode('utf-8')
        m = re.search(r'<a[^>]+?BACK TO MENU[^>]*>', html, flags=re.I)
        print(p, '->', 'FOUND' if m else 'NOT FOUND')
        if m:
            tag = m.group(0)
            href = re.search(r'href\s*=\s*"([^"]*)"', tag)
            onclick = re.search(r'onclick\s*=\s*"([^"]*)"', tag)
            print('  tag:', tag)
            print('  href:', href.group(1) if href else '(no href)')
            print('  onclick:', onclick.group(1) if onclick else '(no onclick)')
    except Exception as e:
        print(p, 'ERROR:', e)
