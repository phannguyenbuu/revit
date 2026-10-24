import urllib.request
import json

url = 'http://127.0.0.1:8096/api/execute'
code = """
(
    local sel = getCurrentSelection()
    local res = #()
    for obj in sel do (
        local cloneObj = copy obj
        convertToPoly cloneObj
        
        local f1Count = 0
        local f2Count = 0
        local f3Count = 0
        local otherCount = 0
        for f = 1 to (polyOp.getNumFaces cloneObj) do (
            local mid = polyOp.getFaceMatID cloneObj f
            if mid == 1 then f1Count += 1
            else if mid == 2 then f2Count += 1
            else if mid == 3 then f3Count += 1
            else otherCount += 1
        )
        
        append res (
            "Obj: " + obj.name + 
            " | Collapsed Min: " + ((cloneObj.min) as string) + 
            " | Collapsed Max: " + ((cloneObj.max) as string) + 
            " | Collapsed Size: " + (((cloneObj.max - cloneObj.min)) as string) + 
            " | Total Faces: " + ((polyOp.getNumFaces cloneObj) as string) +
            " | MatID 1 faces: " + (f1Count as string) + 
            " | MatID 2 faces: " + (f2Count as string) + 
            " | MatID 3 faces: " + (f3Count as string) + 
            " | Other MatID faces: " + (otherCount as string)
        )
        delete cloneObj
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
