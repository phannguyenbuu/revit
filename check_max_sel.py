import urllib.request
import json
import sys

if sys.stdout:
    sys.stdout.reconfigure(encoding='utf-8')

code = """
(
    local res = #()
    for o in selection do (
        append res (o.name + " | pos: " + (o.pos as string) + " | min: " + (o.min as string) + " | max: " + (o.max as string) + " | class: " + ((classof o) as string))
    )
    res
)
"""
req = urllib.request.Request(
    "http://127.0.0.1:8096/api/execute",
    data=json.dumps({"code": code}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
with urllib.request.urlopen(req) as res:
    data = json.loads(res.read().decode('utf-8'))
    print(f"Selection count: {len(data.get('result', []))}")
    for item in data.get('result', []):
        print(" -", item)
