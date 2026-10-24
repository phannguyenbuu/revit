import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Let's inspect walls near entrance or with height around 12300
p = {
    'action': 'query',
    'category': 'walls'
}
req = urllib.request.Request('http://127.0.0.1:8090/api/execute', data=json.dumps(p).encode('utf-8'), headers={'Content-Type': 'application/json'})
resp = json.loads(urllib.request.urlopen(req, timeout=10).read().decode('utf-8'))
elems = resp.get('elements', [])
print('Total walls:', len(elems))
for e in elems:
    name = e.get('name', '')
    if 'trang tri' in name.lower() or 'lam' in name.lower() or 'tru' in name.lower():
        print(e)
