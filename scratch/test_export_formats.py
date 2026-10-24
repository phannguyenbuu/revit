import urllib.request
import json
import os

url = "http://127.0.0.1:8096/api/execute"
code = """
(
    local out = ""
    local tempSat = (getDir #temp) + "\\\\max_selection.sat"
    local tempDwg = (getDir #temp) + "\\\\max_selection.dwg"
    
    if doesFileExist tempSat do deleteFile tempSat
    if doesFileExist tempDwg do deleteFile tempDwg
    
    local resSat = exportFile tempSat #noPrompt selectedOnly:true using:ACIS_SAT
    out += "SAT Export: " + (resSat as string) + " | Exists: " + ((doesFileExist tempSat) as string) + " | Path: " + tempSat + "\\n"
    if doesFileExist tempSat do out += "SAT Size: " + ((getFileSize tempSat) as string) + " bytes\\n"
    
    local resDwg = exportFile tempDwg #noPrompt selectedOnly:true using:DWG_Export
    out += "DWG Export: " + (resDwg as string) + " | Exists: " + ((doesFileExist tempDwg) as string) + " | Path: " + tempDwg + "\\n"
    if doesFileExist tempDwg do out += "DWG Size: " + ((getFileSize tempDwg) as string) + " bytes\\n"
    
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
