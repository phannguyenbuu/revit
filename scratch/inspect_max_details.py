import urllib.request
import json

url = 'http://127.0.0.1:8096/api/execute'
code = """
(
    local sel = getCurrentSelection()
    local res = #()
    for o in sel do (
        local matInfo = if o.material != undefined then (o.material.name + " (" + ((classOf o.material) as string) + ")") else "None"
        local matIds = #()
        if (isKindOf o Editable_Poly) or (isKindOf o PolyMeshObject) do (
            local ids = #{}
            for f = 1 to (polyOp.getNumFaces o) do (
                ids[(polyOp.getFaceMatID o f)] = true
            )
            matIds = ids as array
        )
        local modNames = for m in o.modifiers collect m.name
        append res ("Name: " + o.name + " | Mat: " + matInfo + " | MatIDs: " + (matIds as string) + " | Modifiers: " + (modNames as string) + " | Pos: " + ((o.pos) as string) + " | Min: " + ((o.min) as string) + " | Max: " + ((o.max) as string))
    )
    res
)
"""

req = urllib.request.Request(
    url,
    data=json.dumps({"language": "maxscript", "code": code}).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
        print("Result:", json.dumps(data, indent=2))
except Exception as e:
    print("Error:", e)
