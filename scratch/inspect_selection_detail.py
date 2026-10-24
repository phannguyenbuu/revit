import urllib.request
import json

url = "http://127.0.0.1:8096/api/execute"
code = """
(
    local out = ""
    for o in selection do (
        out += "Name: " + o.name + "\n"
        out += "  Class: " + ((classOf o) as string) + "\n"
        out += "  Pos: " + (o.pos as string) + "\n"
        out += "  BBox Min: " + (o.min as string) + " Max: " + (o.max as string) + "\n"
        out += "  Size: " + ((o.max - o.min) as string) + "\n"
        out += "  Material: " + ((o.material) as string) + "\n"
        out += "  WireColor: " + ((o.wirecolor) as string) + "\n"
        out += "  Num Verts: " + ((getNumVerts o) as string) + " Faces: " + ((getNumFaces o) as string) + "\n"
    )
    
    local selMin = selection.min
    local selMax = selection.max
    out += "TOTAL SELECTION BBOX:\n"
    out += "  Min: " + (selMin as string) + "\n"
    out += "  Max: " + (selMax as string) + "\n"
    out += "  Size: " + ((selMax - selMin) as string) + "\n"
    out
)
"""

req = urllib.request.Request(
    url,
    data=json.dumps({"language": "maxscript", "code": code}).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req) as res:
    data = json.loads(res.read().decode('utf-8'))
    print(data.get("result"))
