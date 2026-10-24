import urllib.request
import json

url = "http://127.0.0.1:8096/api/execute"
code = """
(
    local out = ""
    for obj in selection do (
        out += obj.name + " | class: " + ((classOf obj) as string) + " | pos: " + (obj.pos as string) + " | min: " + (obj.min as string) + " | max: " + (obj.max as string) + "\n"
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
