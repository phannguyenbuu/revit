import urllib.request
import json

url = "http://127.0.0.1:8096/api/execute"
code = """
(
    local out = "Objects along Truc 1 (X ~ -19973.3):\\n"
    for o in objects do (
        if (o.min.x <= -19700 and o.max.x >= -20200) do (
            out += o.name + " | class: " + ((classOf o) as string) + " | bb: [" + (o.min as string) + ", " + (o.max as string) + "]\\n"
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
