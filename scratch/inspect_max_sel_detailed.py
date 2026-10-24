import urllib.request
import json

url = "http://127.0.0.1:8096/api/execute"
code = """
(
    local out = ""
    for o in selection do (
        local bbMin = o.min
        local bbMax = o.max
        local dx = bbMax.x - bbMin.x
        local dy = bbMax.y - bbMin.y
        local dz = bbMax.z - bbMin.z
        local isPoly = (isKindOf o Editable_Poly)
        local canPoly = (canConvertTo o Editable_Poly)
        out += "name: " + o.name + " | class: " + ((classOf o) as string) + " | isPoly: " + (isPoly as string) + " | canPoly: " + (canPoly as string) + " | size: [" + (dx as string) + ", " + (dy as string) + ", " + (dz as string) + "] | min: " + (bbMin as string) + " | max: " + (bbMax as string) + "\\n"
    )
    out
)
"""

req = urllib.request.Request(url, data=json.dumps({"language":"maxscript", "code":code}).encode("utf-8"), headers={"Content-Type":"application/json"})
with urllib.request.urlopen(req) as res:
    data = json.loads(res.read().decode("utf-8"))
    print(data.get("result", data))
