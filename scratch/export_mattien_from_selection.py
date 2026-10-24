import urllib.request
import json

url = 'http://127.0.0.1:8096/api/execute'

code = """
(
    local out = ""
    local sel = getCurrentSelection()
    if sel.count == 0 then (
        out = "ERROR: No object selected in 3ds Max"
    ) else (
        -- Helper for layers
        fn getOrCreateLayer layerName = (
            local lyr = LayerManager.getLayerFromName layerName
            if lyr == undefined do lyr = LayerManager.newLayerFromName layerName
            lyr
        )
        
        local lyrGach1 = getOrCreateLayer "Mat_Tien_Gach_01"
        local lyrGach2 = getOrCreateLayer "Mat_Tien_Gach_02"
        local lyrTuong = getOrCreateLayer "Mat_Tien_Tuong"
        
        local exportNodes = #()
        
        for obj in sel do (
            -- Clone original object
            local cloneObj = copy obj
            convertToPoly cloneObj
            
            -- Detach faces by Mat ID
            -- Mat ID 1
            local f1 = #{}
            for f = 1 to (polyOp.getNumFaces cloneObj) do if (polyOp.getFaceMatID cloneObj f == 1) do f1[f] = true
            if (f1 as array).count > 0 do (
                local name1 = uniqueName "temp_mattien_gach1_"
                polyOp.detachFaces cloneObj f1 asNode:true name:name1
                local nodeGach1 = getNodeByName name1
                if nodeGach1 != undefined do (
                    lyrGach1.addNode nodeGach1
                    nodeGach1.wirecolor = (color 255 255 255)
                    append exportNodes nodeGach1
                )
            )
            
            -- Mat ID 2
            local f2 = #{}
            for f = 1 to (polyOp.getNumFaces cloneObj) do if (polyOp.getFaceMatID cloneObj f == 2) do f2[f] = true
            if (f2 as array).count > 0 do (
                local name2 = uniqueName "temp_mattien_gach2_"
                polyOp.detachFaces cloneObj f2 asNode:true name:name2
                local nodeGach2 = getNodeByName name2
                if nodeGach2 != undefined do (
                    lyrGach2.addNode nodeGach2
                    nodeGach2.wirecolor = (color 255 255 255)
                    append exportNodes nodeGach2
                )
            )
            
            -- Remaining faces in cloneObj are Mat ID 3, 4, etc. (Tuong)
            if (polyOp.getNumFaces cloneObj) > 0 do (
                lyrTuong.addNode cloneObj
                cloneObj.name = uniqueName "temp_mattien_tuong_"
                cloneObj.wirecolor = (color 255 255 255)
                append exportNodes cloneObj
            )
        )
        
        -- Shift by shiftVec
        local shiftVec = [19973.3, 0.0, 0.0]
        for n in exportNodes do move n shiftVec
        
        local dwgPath = (getDir #temp) + "\\\\Mat_Tien_Layered.dwg"
        if doesFileExist dwgPath do deleteFile dwgPath
        
        select exportNodes
        local res = exportFile dwgPath #noPrompt selectedOnly:true
        
        -- Delete temp clones
        delete exportNodes
        
        -- Re-select original selection
        select sel
        
        out = "Exported Layered Mat_Tien DWG: " + (res as string) + " | Path: " + dwgPath + " | Size: " + ((getFileSize dwgPath) as string) + " bytes"
    )
    out
)
"""

req = urllib.request.Request(
    url,
    data=json.dumps({"language": "maxscript", "code": code}).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read().decode('utf-8'))
        print(data.get("result"))
        if "error" in data:
            print("Error:", data["error"])
except Exception as e:
    print("Request Error:", e)
