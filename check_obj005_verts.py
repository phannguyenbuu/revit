import urllib.request
import json

code = """
(
    local o5 = getNodeByName "0725 CAX_obj005"
    if o5 != undefined then (
        local vList = for i = 1 to (polyOp.getNumVerts o5) collect (polyOp.getVert o5 i)
        local minX = 1e9
        local maxX = -1e9
        for v in vList do (
            minX = amin minX v.x
            maxX = amax maxX v.x
        )
        "obj005 Verts: " + (vList.count as string) + " | minX: " + (minX as string) + " | maxX: " + (maxX as string)
    ) else "obj005 not found"
)
"""
req = urllib.request.Request(
    "http://127.0.0.1:8096/api/execute",
    data=json.dumps({"code": code}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
with urllib.request.urlopen(req) as res:
    print(res.read().decode('utf-8'))
