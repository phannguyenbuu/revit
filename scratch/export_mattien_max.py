import urllib.request
import json
import os

url = 'http://127.0.0.1:8096/api/execute'

code = """
(
    local out = ""
    local obj = getNodeByName "0725 CAX_obj005"
    if obj == undefined then (
        out = "ERROR: Object 0725 CAX_obj005 not found"
    ) else (
        -- Record original state
        local origLayer = obj.layer.name
        local origWireColor = obj.wirecolor
        
        -- Create/get dedicated layers
        fn getOrCreateLayer layerName = (
            local lyr = LayerManager.getLayerFromName layerName
            if lyr == undefined do lyr = LayerManager.newLayerFromName layerName
            lyr
        )
        
        local lyrMatTien = getOrCreateLayer "Mat_Tien"
        lyrMatTien.addNode obj
        obj.wirecolor = (color 255 255 255)
        
        -- Shift to origin (X=-19973.3 -> X=0, Y=0 -> Y=0, Z=0 -> Z=0)
        local shiftVec = [19973.3, 0.0, 0.0]
        move obj shiftVec
        
        local dwgPath = (getDir #temp) + "\\\\Mat_Tien_Facade.dwg"
        if doesFileExist dwgPath do deleteFile dwgPath
        
        select #(obj)
        local res = exportFile dwgPath #noPrompt selectedOnly:true
        
        -- Restore position, layer, wirecolor
        move obj (-shiftVec)
        local origLyr = LayerManager.getLayerFromName origLayer
        if origLyr != undefined do origLyr.addNode obj
        obj.wirecolor = origWireColor
        select #(obj)
        
        out = "Exported Mat_Tien DWG: " + (res as string) + " | Path: " + dwgPath + " | Size: " + ((getFileSize dwgPath) as string) + " bytes"
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
    if "error" in data:
        print("Error:", data["error"])
