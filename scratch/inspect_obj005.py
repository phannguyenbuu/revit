import urllib.request
import json

url = 'http://127.0.0.1:8096/api/execute'
code = """
(
    local obj = getNodeByName "0725 CAX_obj005"
    local ss = stringStream ""
    format "Obj: % Class: %\\n" obj.name (classOf obj as string) to:ss
    format "Material: %\\n" (obj.material as string) to:ss
    format "Wirecolor: %\\n" obj.wirecolor to:ss
    
    -- Let's inspect mesh/poly
    local numF = getNumFaces obj
    local numV = getNumVerts obj
    format "NumFaces: % NumVerts: %\\n" numF numV to:ss
    
    -- Check elements
    local ep = obj
    if (isKindOf obj Editable_Poly) or (isKindOf obj PolyMeshObject) then
    (
        local numElements = 0
        local processedFaces = #{}
        local elemList = #()
        for f = 1 to (polyOp.getNumFaces ep) do
        (
            if not (processedFaces[f]) do
            (
                local ef = polyOp.getElementsUsingFace ep #(f)
                processedFaces += ef
                numElements += 1
                
                local minPt = [1e9, 1e9, 1e9]
                local maxPt = [-1e9, -1e9, -1e9]
                local verts = polyOp.getVertsUsingFace ep ef
                for v in verts do
                (
                    local p = polyOp.getVert ep v
                    minPt.x = amin minPt.x p.x; minPt.y = amin minPt.y p.y; minPt.z = amin minPt.z p.z
                    maxPt.x = amax maxPt.x p.x; maxPt.y = amax maxPt.y p.y; maxPt.z = amax maxPt.z p.z
                )
                append elemList #(ef.count, minPt, maxPt, (maxPt - minPt))
            )
        )
        format "Total elements: %\\n" numElements to:ss
        for i = 1 to elemList.count do
        (
            format "Elem %: faces=% min=% max=% size=%\\n" i elemList[i][1] elemList[i][2] elemList[i][3] elemList[i][4] to:ss
        )
    )
    ss as string
)
"""

req = urllib.request.Request(url, data=json.dumps({"code": code}).encode("utf-8"), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as res:
    data = json.loads(res.read().decode("utf-8"))
    print(data.get("result"))
    if "error" in data:
        print("Error:", data["error"])
