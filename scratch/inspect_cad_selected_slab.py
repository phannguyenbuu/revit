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

print(f"Selection count: {pf.Count}")

items = []
for i in range(pf.Count):
    ent = pf.Item(i)
    name = ent.ObjectName
    layer = ent.Layer
    handle = ent.Handle
    
    info = {
        "index": i,
        "objectName": name,
        "layer": layer,
        "handle": handle
    }
    
    try:
        min_pt, max_pt = ent.GetBoundingBox()
        info["bbox"] = {
            "min": [min_pt[0], min_pt[1], min_pt[2]],
            "max": [max_pt[0], max_pt[1], max_pt[2]]
        }
    except Exception as e:
        info["bbox_error"] = str(e)
        
    if name in ["AcDbPolyline", "AcDb2dPolyline"]:
        coords = list(ent.Coordinates)
        info["raw_coords"] = coords
        info["closed"] = ent.Closed
        try:
            info["area"] = ent.Area
        except:
            pass
        # Check bulges
        bulges = []
        num_verts = len(coords) // 2 if name == "AcDbPolyline" else len(coords) // 3
        if name == "AcDbPolyline":
            for v in range(num_verts):
                try:
                    b = ent.GetBulge(v)
                    bulges.append(b)
                except Exception as ex:
                    bulges.append(0.0)
            info["bulges"] = bulges
    elif name == "AcDbHatch":
        try:
            info["area"] = ent.Area
            info["patternName"] = ent.PatternName
        except:
            pass
    elif name == "AcDbRegion":
        try:
            info["area"] = ent.Area
        except:
            pass
            
    items.append(info)

out_file = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\cad_selected_slab.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(items, f, indent=2, ensure_ascii=False)

print(json.dumps(items, indent=2, ensure_ascii=False))
