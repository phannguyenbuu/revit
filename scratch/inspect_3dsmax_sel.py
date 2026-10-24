import json
import urllib.request

url = "http://127.0.0.1:8096/api/execute"

code = """
(
    local ss = stringStream ""
    format "Total selected: %\\n" selection.count to:ss
    for i = 1 to selection.count do
    (
        local obj = selection[i]
        local isInst = #()
        for s in selection do
        (
            if s != obj and (areNodesInstances obj s) do append isInst s.name
        )
        
        local numElements = 0
        local elemDetails = #()
        if (isKindOf obj Editable_Poly) then
        (
            local numFaces = polyOp.getNumFaces obj
            local processedFaces = #{}
            for f = 1 to numFaces do
            (
                if not (processedFaces[f]) do
                (
                    local elemFaces = polyOp.getElementsUsingFace obj #(f)
                    processedFaces += elemFaces
                    numElements += 1
                    local elemArea = 0.0
                    for ef in elemFaces do
                    (
                        elemArea += polyOp.getFaceArea obj ef
                    )
                    append elemDetails #(elemFaces.count, elemArea)
                )
            )
        )
        
        format "Obj %: Name: '%' | Class: % | Pos: % | Min: % | Max: % | Size: % | Rot: % | Elements: % | SelInstances: %\\n" i obj.name (classOf obj as string) obj.pos obj.min obj.max (obj.max - obj.min) obj.rotation numElements isInst to:ss
        for ed = 1 to elemDetails.count do
        (
            format "   Elem %: % faces, Area: %\\n" ed elemDetails[ed][1] elemDetails[ed][2] to:ss
        )
    )
    ss as string
)
"""

payload = json.dumps({"language": "maxscript", "code": code}).encode('utf-8')
req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=30) as res:
    data = json.loads(res.read().decode('utf-8'))
    print(data.get("result"))
    if "error" in data:
        print("Error:", data.get("error"))
