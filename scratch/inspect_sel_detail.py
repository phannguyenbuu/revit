import urllib.request
import json

url = 'http://127.0.0.1:8096/api/execute'
code = """
(
    local ss = stringStream ""
    format "Selection count: %\\n" selection.count to:ss
    for obj in selection do
    (
        format "Name: % | Class: %\\n" obj.name (classOf obj as string) to:ss
        format "  BBox: min=% max=% size=%\\n" obj.min obj.max (obj.max - obj.min) to:ss
        if (isKindOf obj Editable_Poly) then
        (
            format "  Faces: % Verts: %\\n" (polyOp.getNumFaces obj) (polyOp.getNumVerts obj) to:ss
            local selF = (polyOp.getFaceSelection obj) as array
            format "  Selected faces count: %\\n" selF.count to:ss
            local selV = (polyOp.getVertSelection obj) as array
            format "  Selected verts count: %\\n" selV.count to:ss
        )
    )
    format "subObjectLevel: %\\n" subObjectLevel to:ss
    ss as string
)
"""

req = urllib.request.Request(url, data=json.dumps({"code": code}).encode("utf-8"), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as res:
    data = json.loads(res.read().decode("utf-8"))
    print(data.get("result"))
    if "error" in data:
        print("Error:", data["error"])
