import urllib.request
import json

url = "http://127.0.0.1:8096/api/execute"

code = """
(
    local obj = (for o in selection where (o.name == "K2") collect o)[1]
    local tempPath = getDir #temp + "\\\\test_k2.sat"
    select obj
    local res = exportFile tempPath #noPrompt selectedOnly:true using:ACIS_SAT
    format "Export SAT result: % | File exists: %\\n" res (doesFileExist tempPath)
    res
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
