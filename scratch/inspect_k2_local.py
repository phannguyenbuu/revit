import urllib.request
import json

url = "http://127.0.0.1:8096/api/execute"

code = """
(
    local obj = (for o in objects where (o.name == "K2") collect o)[1]
    local ss = stringStream ""
    if obj != undefined do
    (
        -- Get mesh in local space
        local invTm = inverse obj.transform
        local numVerts = polyOp.getNumVerts obj
        local localMin = [1e9, 1e9, 1e9]
        local localMax = [-1e9, -1e9, -1e9]
        for v = 1 to numVerts do
        (
            local worldP = polyOp.getVert obj v
            local localP = worldP * invTm
            if localP.x < localMin.x do localMin.x = localP.x
            if localP.y < localMin.y do localMin.y = localP.y
            if localP.z < localMin.z do localMin.z = localP.z
            if localP.x > localMax.x do localMax.x = localP.x
            if localP.y > localMax.y do localMax.y = localP.y
            if localP.z > localMax.z do localMax.z = localP.z
        )
        format "Local Min: % | Local Max: % | Local Size: %\\n" localMin localMax (localMax - localMin) to:ss
    )
    ss as string
)
"""

req = urllib.request.Request(
    url,
    data=json.dumps({"language": "maxscript", "code": code}).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req, timeout=30) as res:
    data = json.loads(res.read().decode('utf-8'))
    print(data.get("result"))
