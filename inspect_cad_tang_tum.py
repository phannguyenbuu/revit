import sys, ctypes, json
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

pf = doc.PickfirstSelectionSet
if pf.Count == 0:
    pf = doc.ActiveSelectionSet

print(f"Selected entities count: {pf.Count}")

items = []
for i in range(pf.Count):
    ent = pf.Item(i)
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
        coords = list(ent.Coordinates)
        info["coords"] = coords
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
    elif obj_name == "AcDbArc":
        c = ent.Center
        info["center"] = [c[0], c[1], c[2]]
        info["radius"] = ent.Radius
        info["startAngle"] = ent.StartAngle
        info["endAngle"] = ent.EndAngle
    elif obj_name == "AcDbCircle":
        c = ent.Center
        info["center"] = [c[0], c[1], c[2]]
        info["radius"] = ent.Radius

    items.append(info)

out_file = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\cad_selection_tang_tum.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump({"count": len(items), "items": items}, f, indent=2, ensure_ascii=False)

print(f"Saved {len(items)} items to {out_file}")
