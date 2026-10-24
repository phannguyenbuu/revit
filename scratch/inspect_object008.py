import urllib.request
import json

url = "http://127.0.0.1:8096/api/execute"
code = """
(
    local obj = getNodeByName "Object008"
    local numElements = 0
    local visited = #{}
    local numFaces = polyOp.getNumFaces obj
    local out = "Object008 elements:\\n"
    
    for f = 1 to numFaces do (
        if not visited[f] do (
            local elemFaces = polyOp.getElementsUsingFace obj #(f)
            visited += elemFaces
            numElements += 1
            
            -- get bbox of this element
            local elemVerts = polyOp.getVertsUsingFace obj elemFaces
            local minZ = 1e9
            local maxZ = -1e9
            local minX = 1e9
            local maxX = -1e9
            local minY = 1e9
            local maxY = -1e9
            
            for v in elemVerts do (
                local p = polyOp.getVert obj v
                if p.x < minX do minX = p.x
                if p.x > maxX do maxX = p.x
                if p.y < minY do minY = p.y
                if p.y > maxY do maxY = p.y
                if p.z < minZ do minZ = p.z
                if p.z > maxZ do maxZ = p.z
            )
            out += "Elem " + (numElements as string) + ": X[" + (minX as string) + ", " + (maxX as string) + "] Y[" + (minY as string) + ", " + (maxY as string) + "] Z[" + (minZ as string) + ", " + (maxZ as string) + "] Height=" + ((maxZ - minZ) as string) + "\\n"
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
