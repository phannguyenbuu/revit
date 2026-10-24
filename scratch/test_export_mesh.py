import urllib.request
import json

url = "http://127.0.0.1:8096/api/execute"
code = """
(
    local out = ""
    local tempObj = (getDir #temp) + "\\\\max_selection.obj"
    local tempFbx = (getDir #temp) + "\\\\max_selection.fbx"
    local tempDxf = (getDir #temp) + "\\\\max_selection.dxf"
    local temp3ds = (getDir #temp) + "\\\\max_selection.3ds"
    
    if doesFileExist tempObj do deleteFile tempObj
    if doesFileExist tempFbx do deleteFile tempFbx
    if doesFileExist tempDxf do deleteFile tempDxf
    if doesFileExist temp3ds do deleteFile temp3ds
    
    local resObj = exportFile tempObj #noPrompt selectedOnly:true using:ObjExp
    out += "OBJ Export: " + (resObj as string) + " | Exists: " + ((doesFileExist tempObj) as string) + "\\n"
    if doesFileExist tempObj do out += "OBJ Size: " + ((getFileSize tempObj) as string) + " bytes\\n"
    
    local resFbx = exportFile tempFbx #noPrompt selectedOnly:true using:FBXEXP
    out += "FBX Export: " + (resFbx as string) + " | Exists: " + ((doesFileExist tempFbx) as string) + "\\n"
    if doesFileExist tempFbx do out += "FBX Size: " + ((getFileSize tempFbx) as string) + " bytes\\n"
    
    local resDxf = exportFile tempDxf #noPrompt selectedOnly:true
    out += "DXF Export: " + (resDxf as string) + " | Exists: " + ((doesFileExist tempDxf) as string) + "\\n"
    if doesFileExist tempDxf do out += "DXF Size: " + ((getFileSize tempDxf) as string) + " bytes\\n"
    
    local res3ds = exportFile temp3ds #noPrompt selectedOnly:true
    out += "3DS Export: " + (res3ds as string) + " | Exists: " + ((doesFileExist temp3ds) as string) + "\\n"
    if doesFileExist temp3ds do out += "3DS Size: " + ((getFileSize temp3ds) as string) + " bytes\\n"
    
    out
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
