import urllib.request
import json

url = 'http://127.0.0.1:8096/api/execute'
code = """
(
    local obj = getNodeByName "0725 CAX_obj005"
    local matIDs = #{}
    for f = 1 to (polyOp.getNumFaces obj) do
    (
        matIDs[polyOp.getFaceMatID obj f] = true
    )
    matIDs as array
)
"""

req = urllib.request.Request(url, data=json.dumps({"code": code}).encode("utf-8"), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as res:
    data = json.loads(res.read().decode("utf-8"))
    print("Mat IDs:", data.get("result"))
