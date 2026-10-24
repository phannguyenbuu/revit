import sys, ctypes, time, json
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument
print(f"Document: {doc.Name}")

pf = doc.PickfirstSelectionSet
print(f"Pickfirst count: {pf.Count}")

t0 = time.time()
items = []
xs = []
ys = []

for i in range(pf.Count):
    ent = pf.Item(i)
    obj_name = ent.ObjectName
    layer = ent.Layer
    handle = ent.Handle
    
    info = {
        "handle": handle,
        "objectName": obj_name,
        "layer": layer
    }
    
    try:
        p1, p2 = ent.GetBoundingBox()
        info["bb"] = [p1[0], p1[1], p2[0], p2[1]]
        xs.extend([p1[0], p2[0]])
        ys.extend([p1[1], p2[1]])
    except:
        pass
        
    if obj_name == 'AcDbLine':
        sp = ent.StartPoint
        ep = ent.EndPoint
        info["start"] = [sp[0], sp[1]]
        info["end"] = [ep[0], ep[1]]
        info["length"] = ent.Length
    elif 'Polyline' in obj_name:
        info["closed"] = ent.Closed
        info["length"] = ent.Length
    elif obj_name == 'AcDbBlockReference':
        bname = ent.EffectiveName if hasattr(ent, "EffectiveName") else ent.Name
        info["blockName"] = bname
        ins = ent.InsertionPoint
        info["insertion"] = [ins[0], ins[1]]
    elif 'Text' in obj_name:
        info["text"] = ent.TextString
        ins = ent.InsertionPoint
        info["insertion"] = [ins[0], ins[1]]
        if hasattr(ent, "Height"):
            info["height"] = ent.Height
            
    items.append(info)

dt = time.time() - t0
print(f"Extracted {len(items)} items in {dt:.2f}s")
min_x, max_x = min(xs), max(xs)
min_y, max_y = min(ys), max(ys)
print(f"Selection CAD bounds: X=[{min_x:.1f}, {max_x:.1f}], Y=[{min_y:.1f}, {max_y:.1f}]")
print(f"Width = {max_x - min_x:.1f}, Height = {max_y - min_y:.1f}")

out_file = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\cad_tang3_extracted.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump({
        "count": len(items),
        "bounds": [min_x, min_y, max_x, max_y],
        "items": items
    }, f, indent=2, ensure_ascii=False)

print(f"Saved to {out_file}")
