"""Import the requested Suction Cup OBJ folder as a spaced rectangle row."""
import json
from pathlib import Path
from max_cli import request_json

FOLDER = Path(r'D:/Dropbox/_Documents/_Vlance_2026/Aardwolf/ref/3D Step/3D Step/Suction Cup/OBJ')


def main():
    files = sorted(FOLDER.glob('*.obj'), key=lambda p: p.name.lower())
    for index, path in enumerate(files):
        low, high = [float('inf')]*3, [float('-inf')]*3
        for line in path.open(errors='replace'):
            if line.startswith('v '):
                for k, value in enumerate(map(float, line.split()[1:4])):
                    low[k], high[k] = min(low[k], value), max(high[k], value)
        source_span = max(high[k]-low[k] for k in range(3))
        code = r'''(
            local sourcePath = @"PATH"
            local assetName = @"ASSET"
            local centerX = INDEX * 6000.0
            local alreadyDone = false
            for item in SuctionObjBatchResults where item[1] == assetName do alreadyDone = true
            if alreadyDone then ("Already imported: " + assetName) else
            (
                local oldHandles = for n in objects collect (getHandleByAnim n)
                local imported = #()
                local rect
                undo "Import OBJ into rectangle" on
                (
                    try
                    (
                        local ok = importFile sourcePath #noPrompt using:ObjImp
                        imported = for n in objects where (findItem oldHandles (getHandleByAnim n)) == 0 collect n
                        if imported.count == 0 then throw "OBJ import created no nodes"
                        local lower = [1e20,1e20,1e20]
                        local upper = [-1e20,-1e20,-1e20]
                        for n in imported do
                        (
                            local bb = nodeGetBoundingBox n (matrix3 1)
                            for k=1 to 3 do (lower[k] = amin lower[k] bb[1][k]; upper[k] = amax upper[k] bb[2][k])
                        )
                        local spans = upper-lower
                        local unitFactor = SOURCESPAN / (amax spans.x (amax spans.y spans.z))
                        for n in imported where n.parent == undefined or (findItem imported n.parent) == 0 do scale n [unitFactor,unitFactor,unitFactor]
                        lower = [1e20,1e20,1e20]
                        upper = [-1e20,-1e20,-1e20]
                        for n in imported do
                        (
                            local bb = nodeGetBoundingBox n (matrix3 1)
                            for k=1 to 3 do (lower[k] = amin lower[k] bb[1][k]; upper[k] = amax upper[k] bb[2][k])
                        )
                        if (upper.x-lower.x) > 4000 or (upper.y-lower.y) > 4000 then throw "OBJ exceeds 4000x4000"
                        local delta = [centerX-(lower.x+upper.x)/2, SuctionObjBatchY-(lower.y+upper.y)/2, -lower.z]
                        for n in imported where n.parent == undefined or (findItem imported n.parent) == 0 do move n delta
                        rect = rectangle name:assetName width:4000 length:4000 cornerRadius:0 pos:[centerX,SuctionObjBatchY,0]
                        setUserProp rect "AI_SourceOBJ" sourcePath
                        local assetLayer = LayerManager.getLayerFromName ("Suction_"+assetName)
                        if assetLayer == undefined do assetLayer = LayerManager.newLayerFromName ("Suction_"+assetName)
                        assetLayer.addNode rect
                        for k=1 to imported.count do
                        (
                            local n=imported[k]
                            n.name = uniqueName (assetName+"_mesh_")
                            setUserProp n "AI_SourceOBJ" sourcePath
                            assetLayer.addNode n
                        )
                        append SuctionObjBatchResults #(assetName,rect.name,imported.count,centerX,SuctionObjBatchY,upper-lower)
                        redrawViews()
                    )
                    catch
                    (
                        imported = for n in objects where (findItem oldHandles (getHandleByAnim n)) == 0 collect n
                        for n in imported where isValidNode n do delete n
                        throw()
                    )
                )
                (SuctionObjBatchResults[SuctionObjBatchResults.count]) as string
            )
        )'''.replace('PATH', str(path)).replace('ASSET', path.stem).replace('INDEX', str(index)).replace('SOURCESPAN', repr(source_span))
        result = request_json('/api/execute', {'language': 'maxscript', 'code': code})
        print(json.dumps({'index': index+1, 'file':path.name, 'response': result}, ensure_ascii=True), flush=True)
        if not result.get('success'):
            raise RuntimeError('Import did not confirm success; inspect bridge state before retrying.')


if __name__ == '__main__':
    main()
