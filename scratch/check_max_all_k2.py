import urllib.request
import json

url = "http://127.0.0.1:8096/api/execute"
code = """
(
    local objs = for o in objects where (o.name == "K2" or o.name == "Object008") collect o
    local out = ""
    for o in objs do (
        out += o.name + " | pos: " + (o.pos as string) + " | min: " + (o.min as string) + " | max: " + (o.max as string) + "\n"
    )
    out
)
"""

req = urllib.request.Request(
    url,
    data=json.dumps({"language": "maxscript", "code": code}).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req) as res:
    print(res.read().decode('utf-8'))
