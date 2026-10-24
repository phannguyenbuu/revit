import urllib.request
import json

code = """
(
    local lines = #()
    for o in selection do (
        append lines (o.name + " | X: [" + (o.min.x as string) + " .. " + (o.max.x as string) + "] | Y: [" + (o.min.y as string) + " .. " + (o.max.y as string) + "] | Z: [" + (o.min.z as string) + " .. " + (o.max.z as string) + "]")
    )
    lines
)
"""
req = urllib.request.Request(
    "http://127.0.0.1:8096/api/execute",
    data=json.dumps({"code": code}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
with urllib.request.urlopen(req) as res:
    data = json.loads(res.read().decode('utf-8'))
    for l in data.get("result", []):
        print(l)
