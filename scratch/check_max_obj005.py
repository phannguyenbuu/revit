import urllib.request
import json

url = "http://127.0.0.1:8096/api/execute"
code = """
(
    local out = "Mesh elements near Truc 1 (X ~ -19973.3):\\n"
    -- Look at 0725 CAX_obj005
    local obj = getNodeByName "0725 CAX_obj005"
    if obj != undefined do (
        out += "0725 CAX_obj005 numFaces: " + ((polyOp.getNumFaces obj) as string) + "\\n"
        -- find elements near X=-19973.3 and Y between 4000 and 7000
        local visited = #{}
        local numFaces = polyOp.getNumFaces obj
        for f = 1 to numFaces do (
            if not visited[f] do (
                local elemFaces = polyOp.getElementsUsingFace obj #(f)
                visited += elemFaces
                local elemVerts = polyOp.getVertsUsingFace obj elemFaces
                local minX = 1e9; local maxX = -1e9
                local minY = 1e9; local maxY = -1e9
                local minZ = 1e9; local maxZ = -1e9
                for v in elemVerts do (
                    local p = polyOp.getVert obj v
                    if p.x < minX do minX = p.x; if p.x > maxX do maxX = p.x
                    if p.y < minY do minY = p.y; if p.y > maxY do maxY = p.y
                    if p.z < minZ do minZ = p.z; if p.z > maxZ do maxZ = p.z
                )
                if (maxX >= -20200 and minX <= -19700 and maxY >= 4500 and minY <= 7000) do (
                    out += "Elem (faces=" + ((elemFaces as array).count as string) + ") X[" + (minX as string) + ", " + (maxX as string) + "] Y[" + (minY as string) + ", " + (maxY as string) + "] Z[" + (minZ as string) + ", " + (maxZ as string) + "]\\n"
                )
            )
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
