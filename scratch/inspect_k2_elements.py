import urllib.request
import json

url = "http://127.0.0.1:8096/api/execute"

code = """
(
    local obj = (for o in selection where (o.name == "K2") collect o)[1]
    local ss = stringStream ""
    if obj != undefined do
    (
        format "Window Name: % | Pos: % | Min: % | Max: % | Size: %\\n" obj.name obj.pos obj.min obj.max (obj.max - obj.min) to:ss
        
        -- Let's inspect each element's local bbox (in obj's local coordinate system)
        local numFaces = polyOp.getNumFaces obj
        local processedFaces = #{}
        local elemIdx = 0
        for f = 1 to numFaces do
        (
            if not (processedFaces[f]) do
            (
                local elemFaces = polyOp.getElementsUsingFace obj #(f)
                processedFaces += elemFaces
                elemIdx += 1
                
                local minPt = [1e9, 1e9, 1e9]
                local maxPt = [-1e9, -1e9, -1e9]
                local elemVerts = polyOp.getVertsUsingFace obj elemFaces
                for v in elemVerts do
                (
                    local p = polyOp.getVert obj v
                    if p.x < minPt.x do minPt.x = p.x
                    if p.y < minPt.y do minPt.y = p.y
                    if p.z < minPt.z do minPt.z = p.z
                    if p.x > maxPt.x do maxPt.x = p.x
                    if p.y > maxPt.y do maxPt.y = p.y
                    if p.z > maxPt.z do maxPt.z = p.z
                )
                
                local area = 0.0
                for ef in elemFaces do area += polyOp.getFaceArea obj ef
                format "Element %: Verts: % | Faces: % | Area: % | Min: % | Max: % | Size: %\\n" elemIdx elemVerts.count elemFaces.count area minPt maxPt (maxPt - minPt) to:ss
            )
        )
    )
    ss as string
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
