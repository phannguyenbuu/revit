import urllib.request
import json

url = 'http://127.0.0.1:8096/api/execute'

code = """
(
    local out = ""
    local obj = getNodeByName "0725 CAX_obj005"
    if obj == undefined then (
        out = "ERROR: Object 0725 CAX_obj005 not found"
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
        
        -- Clone original object
        local cloneObj = copy obj
        convertToPoly cloneObj
        
        -- Detach faces by Mat ID
        -- Mat ID 1
        local f1 = #{}
        for f = 1 to (polyOp.getNumFaces cloneObj) do if (polyOp.getFaceMatID cloneObj f == 1) do f1[f] = true
        polyOp.detachFaces cloneObj f1 asNode:true name:"temp_mattien_gach1"
        local nodeGach1 = getNodeByName "temp_mattien_gach1"
        if nodeGach1 != undefined do (
            lyrGach1.addNode nodeGach1
            nodeGach1.wirecolor = (color 255 255 255)
        )
        
        -- Mat ID 2
        local f2 = #{}
        for f = 1 to (polyOp.getNumFaces cloneObj) do if (polyOp.getFaceMatID cloneObj f == 2) do f2[f] = true
        polyOp.detachFaces cloneObj f2 asNode:true name:"temp_mattien_gach2"
        local nodeGach2 = getNodeByName "temp_mattien_gach2"
        if nodeGach2 != undefined do (
            lyrGach2.addNode nodeGach2
            nodeGach2.wirecolor = (color 255 255 255)
        )
        
        -- Remaining faces in cloneObj are Mat ID 3 and 4 (Tuong)
        lyrTuong.addNode cloneObj
        cloneObj.name = "temp_mattien_tuong"
        cloneObj.wirecolor = (color 255 255 255)
        
        local exportNodes = #()
        if nodeGach1 != undefined do append exportNodes nodeGach1
        if nodeGach2 != undefined do append exportNodes nodeGach2
        append exportNodes cloneObj
        
        -- Shift by shiftVec
        local shiftVec = [19973.3, 0.0, 0.0]
        for n in exportNodes do move n shiftVec
        
        local dwgPath = (getDir #temp) + "\\\\Mat_Tien_Layered.dwg"
        if doesFileExist dwgPath do deleteFile dwgPath
        
        select exportNodes
        local res = exportFile dwgPath #noPrompt selectedOnly:true
        
        -- Delete temp clones
        delete exportNodes
        
        -- Re-select original obj
        select #(obj)
        
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

with urllib.request.urlopen(req) as res:
    data = json.loads(res.read().decode('utf-8'))
    print(data.get("result"))
    if "error" in data:
        print("Error:", data["error"])
