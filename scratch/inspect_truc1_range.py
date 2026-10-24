import urllib.request
import json

url = "http://127.0.0.1:8096/api/execute"
code = """
(
    local out = ""
    for o in objects do (
        if (o.min.x <= -19800 and o.max.x >= -20100 and o.max.y >= 3000 and o.min.y <= 7000) do (
            out += o.name + " | " + ((classOf o) as string) + " | bb: [" + (o.min as string) + ", " + (o.max as string) + "] | mat: " + ((o.material) as string) + "\\n"
        )
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
