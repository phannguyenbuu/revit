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

selected_entities = []
if pf.Count > 0:
    for i in range(pf.Count):
        selected_entities.append(pf.Item(i))
else:
    act = doc.ActiveSelectionSet
    print(f"ActiveSelectionSet count: {act.Count}")
    for i in range(act.Count):
        selected_entities.append(act.Item(i))

print(f"Total: {len(selected_entities)}")

items = []
for idx, ent in enumerate(selected_entities):
    obj_name = ent.ObjectName
    layer = ent.Layer
    handle = ent.Handle
    p1, p2 = ent.GetBoundingBox()
    
    item = {
        "index": idx,
        "objectName": obj_name,
        "layer": layer,
        "handle": handle,
        "bb_min": [p1[0], p1[1]],
        "bb_max": [p2[0], p2[1]]
    }
    
    if obj_name == 'AcDbLine':
        sp = ent.StartPoint
        ep = ent.EndPoint
        item["start"] = [sp[0], sp[1]]
        item["end"] = [ep[0], ep[1]]
        item["length"] = ent.Length
    elif 'Polyline' in obj_name:
        coords = list(ent.Coordinates)
        pts = [[coords[j], coords[j+1]] for j in range(0, len(coords), 2)]
        item["coords"] = pts
        item["closed"] = ent.Closed
        item["length"] = ent.Length
    elif obj_name == 'AcDbBlockReference':
        item["blockName"] = ent.EffectiveName if hasattr(ent, "EffectiveName") else ent.Name
        ins = ent.InsertionPoint
        item["insertion"] = [ins[0], ins[1]]
    elif 'Text' in obj_name:
        item["text"] = ent.TextString
        ins = ent.InsertionPoint
        item["insertion"] = [ins[0], ins[1]]
        
    items.append(item)

out_file = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\selected_3walls_1door.json"
with open(out_file, 'w', encoding='utf-8') as f:
    json.dump(items, f, indent=2, ensure_ascii=False)

print(f"Wrote {len(items)} items to {out_file}")

# Print summary by layer and objectName
summary = {}
for it in items:
    key = f"{it['layer']} | {it['objectName']}"
    summary[key] = summary.get(key, 0) + 1

for k, v in summary.items():
    print(f"  {k}: {v}")
