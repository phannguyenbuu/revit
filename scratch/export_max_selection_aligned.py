import urllib.request
import json
import os

url = "http://127.0.0.1:8096/api/execute"
code = """
(
    local out = ""
    local sel = selection as array
    if sel.count == 0 then (
        out = "ERROR: No objects selected in 3ds Max"
    ) else (
        -- Calculate bounding box
        local bmin = sel[1].min
        local bmax = sel[1].max
        for o in sel do (
            bmin.x = amin bmin.x o.min.x
            bmin.y = amin bmin.y o.min.y
            bmin.z = amin bmin.z o.min.z
            bmax.x = amax bmax.x o.max.x
            bmax.y = amax bmax.y o.max.y
            bmax.z = amax bmax.z o.max.z
        )
        
        -- The wall line is at -19973.3, Y center is 0, Z base is 0
        local shiftVec = [19973.3, 0.0, 0.0]
        
        -- Shift objects to origin
        for o in sel do move o shiftVec
        
        local dwgPath = (getDir #temp) + "\\\\Sanh_Chinh_Origin.dwg"
        if doesFileExist dwgPath do deleteFile dwgPath
        
        select sel
        local res = exportFile dwgPath #noPrompt selectedOnly:true
        
        -- Restore position
        for o in sel do move o (-shiftVec)
        
        out = "Export: " + (res as string) + " | Path: " + dwgPath + " | Size: " + ((getFileSize dwgPath) as string) + " bytes"
    )
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
