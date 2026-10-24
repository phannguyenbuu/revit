import sys
import json
import win32com.client

try:
    acad = win32com.client.GetActiveObject("AutoCAD.Application")
    doc = acad.ActiveDocument
    selection = doc.ActiveSelectionSet
    
    print(f"ActiveSelectionSet Count: {selection.Count}")
    
    items = []
    for i in range(selection.Count):
        ent = selection.Item(i)
        obj_name = ent.ObjectName
        layer = ent.Layer
        handle = ent.Handle
        
        info = {
            "index": i,
            "handle": handle,
            "objectName": obj_name,
            "layer": layer
        }
        
        try:
            min_pt, max_pt = ent.GetBoundingBox()
            info["bbox"] = {
                "min": [min_pt[0], min_pt[1], min_pt[2]],
                "max": [max_pt[0], max_pt[1], max_pt[2]]
            }
        except Exception as e:
            info["bbox_error"] = str(e)
            
        if obj_name == "AcDbLine":
            sp = ent.StartPoint
            ep = ent.EndPoint
            info["start"] = [sp[0], sp[1], sp[2]]
            info["end"] = [ep[0], ep[1], ep[2]]
        elif obj_name == "AcDbPolyline":
            coords = ent.Coordinates
            info["coords"] = list(coords)
            info["closed"] = ent.Closed
        elif obj_name == "AcDbBlockReference":
            info["blockName"] = ent.EffectiveName if hasattr(ent, "EffectiveName") else ent.Name
            ins = ent.InsertionPoint
            info["insertion"] = [ins[0], ins[1], ins[2]]
            info["rotation"] = ent.Rotation
        elif obj_name in ["AcDbText", "AcDbMText"]:
            info["text"] = ent.TextString
            ins = ent.InsertionPoint
            info["insertion"] = [ins[0], ins[1], ins[2]]

        items.append(info)
        
    out_file = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\current_cad_selection.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"count": len(items), "items": items}, f, indent=2, ensure_ascii=False)
        
    print(f"Saved {len(items)} items to {out_file}")
    for it in items[:15]:
        print(f"- {it.get('objectName')}, layer: {it.get('layer')}, block/text: {it.get('blockName') or it.get('text', '')}, bbox: {it.get('bbox')}")
        
except Exception as ex:
    print(f"Error: {ex}", file=sys.stderr)
