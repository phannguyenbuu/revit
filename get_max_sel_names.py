import urllib.request
import json
import re

req = urllib.request.Request(
    "http://127.0.0.1:8096/api/execute",
    data=json.dumps({"code": "(for o in selection collect o.name)"}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
with urllib.request.urlopen(req) as res:
    data = json.loads(res.read().decode('utf-8'))
    raw = data.get("result", "")
    names = re.findall(r'"([^"]+)"', raw)
    print(f"Total selected objects in 3ds Max: {len(names)}")
    for n in names:
        print(" *", n)
