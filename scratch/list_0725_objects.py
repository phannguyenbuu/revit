import urllib.request
import json

url = 'http://127.0.0.1:8096/api/execute'
code = """
(
    local ss = stringStream ""
    format "All objects matching 0725 CAX*:\\n" to:ss
    for o in objects do
    (
        if matchPattern o.name pattern:"0725 CAX*" do
        (
            format "  % (class: %, isHidden: %, isFrozen: %, min: %, max: %)\\n" o.name (classOf o as string) o.isHidden o.isFrozen o.min o.max to:ss
        )
    )
    ss as string
)
"""

req = urllib.request.Request(url, data=json.dumps({"code": code}).encode("utf-8"), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as res:
    data = json.loads(res.read().decode("utf-8"))
    print(data.get("result"))
