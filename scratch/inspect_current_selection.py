import urllib.request
import json

url = "http://127.0.0.1:8096/api/execute"
code = """
(
    local out = ""
    for o in selection do (
        out += o.name + " | class: " + ((classOf o) as string) + \
               " | verts: " + (o.numverts as string) + \
               " | faces: " + (o.numfaces as string) + \
               " | min: " + (o.min as string) + \
               " | max: " + (o.max as string) + "\\n"
    )
    out
)
"""

req = urllib.request.Request(url, data=json.dumps({"language":"maxscript", "code":code}).encode("utf-8"), headers={"Content-Type":"application/json"})
with urllib.request.urlopen(req) as res:
    data = json.loads(res.read().decode("utf-8"))
    print(data.get("result", data))
