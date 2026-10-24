import urllib.request
import json

url = "http://127.0.0.1:8096/api/execute"

code = """
(
    local obj = (for o in objects where (o.name == "K2") collect o)[1]
    select obj
    local dwgPath = getDir #temp + "\\\\test_k2.dwg"
    local dxfPath = getDir #temp + "\\\\test_k2.dxf"
    local objPath = getDir #temp + "\\\\test_k2.obj"
    
    local rDwg = exportFile dwgPath #noPrompt selectedOnly:true using:DWG_Export
    local rDxf = exportFile dxfPath #noPrompt selectedOnly:true
    local rObj = exportFile objPath #noPrompt selectedOnly:true using:ObjExp
    
    #(
        "dwg: " + (doesFileExist dwgPath) as string + " (" + (getFileSize dwgPath) as string + " bytes)",
        "dxf: " + (doesFileExist dxfPath) as string + " (" + (getFileSize dxfPath) as string + " bytes)",
        "obj: " + (doesFileExist objPath) as string + " (" + (getFileSize objPath) as string + " bytes)"
    )
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
