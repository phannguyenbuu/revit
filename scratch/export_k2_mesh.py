import urllib.request
import json
import os

url = "http://127.0.0.1:8096/api/execute"

code = """
(
    local obj = (for o in objects where (o.name == "K2") collect o)[1]
    local ss = stringStream ""
    if obj != undefined do
    (
        local invTm = inverse obj.transform
        local numFaces = polyOp.getNumFaces obj
        local processedFaces = #{}
        
        -- Identify glass element (largest area) vs frame elements
        local elemList = #()
        for f = 1 to numFaces do
        (
            if not (processedFaces[f]) do
            (
                local elemFaces = polyOp.getElementsUsingFace obj #(f)
                processedFaces += elemFaces
                local area = 0.0
                for ef in elemFaces do area += polyOp.getFaceArea obj ef
                append elemList #(elemFaces, area)
            )
        )
        
        -- Sort elements by area descending
        -- The largest is Glass (index 1), rest are Frame
        local maxArea = -1.0
        local glassElemFaces = #()
        local frameElemFaces = #{}
        
        for e in elemList do
        (
            if e[2] > maxArea then
            (
                maxArea = e[2]
                glassElemFaces = e[1]
            )
        )
        
        for e in elemList do
        (
            if e[1] != glassElemFaces do frameElemFaces += e[1]
        )
        
        -- Function to extract vertices and faces for a face set
        -- Returns formatted json chunk
        format "{\\n" to:ss
        
        -- 1. Glass
        format "  \\"glass\\": {\\n" to:ss
        local gVerts = polyOp.getVertsUsingFace obj glassElemFaces
        local gVertMap = #()
        local gVertList = #()
        local vIdx = 0
        for v in gVerts do
        (
            vIdx += 1
            gVertMap[v] = vIdx
            local p = (polyOp.getVert obj v) * invTm
            -- offset Z by +1800 so bottom is at Z=0
            p.z += 1800.0
            append gVertList p
        )
        format "    \\"vertices\\": [" to:ss
        for i = 1 to gVertList.count do
        (
            local p = gVertList[i]
            format "[%, %, %]%" (formattedPrint p.x format:".4f") (formattedPrint p.y format:".4f") (formattedPrint p.z format:".4f") (if i < gVertList.count then ", " else "") to:ss
        )
        format "],\\n" to:ss
        
        format "    \\"faces\\": [" to:ss
        local gFaceList = glassElemFaces as array
        for i = 1 to gFaceList.count do
        (
            local f = gFaceList[i]
            local fv = polyOp.getFaceVerts obj f
            format "[" to:ss
            for j = 1 to fv.count do
            (
                format "%" (gVertMap[fv[j]] - 1) to:ss
                if j < fv.count do format ", " to:ss
            )
            format "]%" (if i < gFaceList.count then ", " else "") to:ss
        )
        format "]\\n  },\\n" to:ss
        
        -- 2. Frame
        format "  \\"frame\\": {\\n" to:ss
        local fVerts = polyOp.getVertsUsingFace obj frameElemFaces
        local fVertMap = #()
        local fVertList = #()
        vIdx = 0
        for v in fVerts do
        (
            vIdx += 1
            fVertMap[v] = vIdx
            local p = (polyOp.getVert obj v) * invTm
            p.z += 1800.0
            append fVertList p
        )
        format "    \\"vertices\\": [" to:ss
        for i = 1 to fVertList.count do
        (
            local p = fVertList[i]
            format "[%, %, %]%" (formattedPrint p.x format:".4f") (formattedPrint p.y format:".4f") (formattedPrint p.z format:".4f") (if i < fVertList.count then ", " else "") to:ss
        )
        format "],\\n" to:ss
        
        format "    \\"faces\\": [" to:ss
        local fFaceList = frameElemFaces as array
        for i = 1 to fFaceList.count do
        (
            local f = fFaceList[i]
            local fv = polyOp.getFaceVerts obj f
            format "[" to:ss
            for j = 1 to fv.count do
            (
                format "%" (fVertMap[fv[j]] - 1) to:ss
                if j < fv.count do format ", " to:ss
            )
            format "]%" (if i < fFaceList.count then ", " else "") to:ss
        )
        format "]\\n  }\\n}" to:ss
    )
    ss as string
)
"""

req = urllib.request.Request(
    url,
    data=json.dumps({"language": "maxscript", "code": code}).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req, timeout=45) as res:
    data = json.loads(res.read().decode('utf-8'))
    json_str = data.get("result")
    out_file = r"d:\Dropbox\_Documents\RevitAI\scratch\k2_mesh.json"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(json_str)
    print("Saved mesh to", out_file)
    print("File size:", os.path.getsize(out_file), "bytes")
