import urllib.request
import json

url = "http://127.0.0.1:8096/api/execute"
code = """
(
    local out = ""
    local validObjs = #()
    for o in selection do (
        if (isKindOf o Editable_Poly) do (
            local bbMin = o.min
            local bbMax = o.max
            local dx = bbMax.x - bbMin.x
            local dy = bbMax.y - bbMin.y
            local dz = bbMax.z - bbMin.z
            if (dx > 10.0 and dy > 10.0 and dz > 10.0) do (
                append validObjs o
            )
        )
    )
    
    if validObjs.count == 0 then (
        out = "ERROR: No valid Editable_Poly objects found in selection"
    ) else (
        -- Record original layers
        local origLayers = for o in validObjs collect o.layer.name
        
        -- Create/get dedicated layers
        fn getOrCreateLayer layerName = (
            local lyr = LayerManager.getLayerFromName layerName
            if lyr == undefined do lyr = LayerManager.newLayerFromName layerName
            lyr
        )
        
        local lyrCot = getOrCreateLayer "Cot_Sanh"
        local lyrMai = getOrCreateLayer "Mai_Sanh"
        local lyrSan = getOrCreateLayer "San_Sanh"
        local lyrBac = getOrCreateLayer "Bac_Tam_Cap"
        
        for o in validObjs do (
            local n = o.name
            if (findString n "obj003" != undefined and findString n "40cbcs" != undefined) or \
               (findString n "obj004" != undefined) or \
               (findString n "obj040" != undefined) or \
               (findString n "obj041" != undefined) then (
                lyrCot.addNode o
            ) else if (findString n "0725 CAX_obj003" != undefined) then (
                lyrMai.addNode o
            ) else if (findString n "Object005" != undefined) or \
                      (findString n "CAX_obj008" != undefined) then (
                lyrBac.addNode o
            ) else (
                lyrSan.addNode o
            )
        )
        
        local shiftVec = [19973.3, 0.0, 0.0]
        for o in validObjs do move o shiftVec
        
        local dwgPath = (getDir #temp) + "\\\\Sanh_Chinh_Layered.dwg"
        if doesFileExist dwgPath do deleteFile dwgPath
        
        select validObjs
        local res = exportFile dwgPath #noPrompt selectedOnly:true
        
        -- Restore positions
        for o in validObjs do move o (-shiftVec)
        
        -- Restore original layers
        for i = 1 to validObjs.count do (
            local origLyr = LayerManager.getLayerFromName origLayers[i]
            if origLyr != undefined do origLyr.addNode validObjs[i]
        )
        
        -- Reselect original selection
        select validObjs
        
        local fSize = getFileSize dwgPath
        out = "OK: Exported " + (validObjs.count as string) + " Editable_Poly objects | File: " + dwgPath + " | Size: " + (fSize as string) + " bytes"
    )
    out
)
"""

req = urllib.request.Request(url, data=json.dumps({"language":"maxscript", "code":code}).encode("utf-8"), headers={"Content-Type":"application/json"})
with urllib.request.urlopen(req) as res:
    data = json.loads(res.read().decode("utf-8"))
    print(data.get("result", data))
