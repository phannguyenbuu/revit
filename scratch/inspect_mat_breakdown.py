import urllib.request
import json

url = 'http://127.0.0.1:8096/api/execute'
code = """
(
    local obj = getNodeByName "0725 CAX_obj005"
    local ss = stringStream ""
    format "Material name: %\\n" (obj.material.name) to:ss
    if isKindOf obj.material Multimaterial then
    (
        for i = 1 to obj.material.numsubs do
        (
            format "  SubMat %: % (name: %)\\n" i (classOf obj.material[i] as string) (obj.material[i].name) to:ss
        )
    )
    
    -- Count faces per Mat ID
    local idCounts = #(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    for f = 1 to (polyOp.getNumFaces obj) do
    (
        local mid = polyOp.getFaceMatID obj f
        if mid <= idCounts.count then idCounts[mid] += 1
    )
    for i = 1 to idCounts.count do
    (
        if idCounts[i] > 0 do
            format "  MatID % count: % faces\\n" i idCounts[i] to:ss
    )
    ss as string
)
"""

req = urllib.request.Request(url, data=json.dumps({"code": code}).encode("utf-8"), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as res:
    data = json.loads(res.read().decode("utf-8"))
    print(data.get("result"))
