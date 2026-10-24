import urllib.request
import json

url = "http://127.0.0.1:8096/api/execute"
code = """
(
    local tempDwg = (getDir #temp) + "\\\\max_selection_test.dwg"
    if doesFileExist tempDwg do deleteFile tempDwg
    local res = exportFile tempDwg #noPrompt selectedOnly:true
    format "DWG by ext: % | Exists: % | Size: %\n" res (doesFileExist tempDwg) (if doesFileExist tempDwg then (getFileSize tempDwg) else 0)
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
