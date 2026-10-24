import sys, ctypes, time, json
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = None
for d in acad.Documents:
    if 'LONG TIÊN' in d.Name:
        doc = d
        break
if not doc:
    doc = acad.ActiveDocument

print(f"Document: {doc.Name}")

pf = doc.PickfirstSelectionSet
print(f"Pickfirst count: {pf.Count}")

selected = []
if pf.Count > 0:
    for i in range(pf.Count):
        selected.append(pf.Item(i))
else:
    act = doc.ActiveSelectionSet
    for i in range(act.Count):
        selected.append(act.Item(i))

print(f"Total items: {len(selected)}")

# Group by ObjectName and Layer
by_type = {}
by_layer = {}
items = []

for idx, ent in enumerate(selected):
    obj_name = ent.ObjectName
    layer = ent.Layer
    by_type[obj_name] = by_type.get(obj_name, 0) + 1
    by_layer[layer] = by_layer.get(layer, 0) + 1

    p1, p2 = ent.GetBoundingBox()
    item_info = {
        "idx": idx,
        "type": obj_name,
        "layer": layer,
        "handle": ent.Handle,
        "box_cad": [p1[0], p1[1], p2[0], p2[1]],
        "box_rvt": [
            round((p1[0] + 132847.0) / 1000.0, 4),
            round((p1[1] + 1400405.9) / 1000.0, 4),
            round((p2[0] + 132847.0) / 1000.0, 4),
            round((p2[1] + 1400405.9) / 1000.0, 4)
        ]
    }

    if "Text" in obj_name:
        item_info["text"] = ent.TextString
    elif obj_name == "AcDbBlockReference":
        name = ent.EffectiveName if hasattr(ent, "EffectiveName") else ent.Name
        item_info["block_name"] = name
        if ent.HasAttributes:
            attrs = {att.TagString: att.TextString for att in ent.GetAttributes()}
            item_info["attrs"] = attrs
    elif "Polyline" in obj_name:
        coords = list(ent.Coordinates)
        pts = [(coords[j], coords[j+1]) for j in range(0, len(coords), 2)]
        item_info["closed"] = ent.Closed
        item_info["length"] = round(ent.Length, 3)
        item_info["vertices_count"] = len(pts)
        item_info["pts_rvt"] = [
            [round((vx + 132847.0) / 1000.0, 4), round((vy + 1400405.9) / 1000.0, 4)]
            for vx, vy in pts
        ]

    items.append(item_info)

print("\n--- Summary by ObjectType ---")
for t, c in by_type.items():
    print(f"  {t}: {c}")

print("\n--- Summary by Layer ---")
for l, c in by_layer.items():
    print(f"  {l}: {c}")

# Find any text or tags
texts = [it for it in items if "text" in it or "attrs" in it]
print(f"\n--- Found {len(texts)} text/tag items ---")
for t in texts:
    print(f"  Layer {t['layer']}: Text='{t.get('text')}' Attrs={t.get('attrs')} BoxRvt={t['box_rvt']}")

# Find walls (Polylines on wall layers like S5, S4, S2, TƯỜNG, etc.)
wall_layers = [it for it in items if it['layer'] in ['S5', 'S4', 'S3', 'S2', 'S1', 'TUONG', 'TƯỜNG']]
print(f"\n--- Items on wall-like layers ({len(wall_layers)}) ---")
for w in wall_layers:
    print(f"  Handle: {w['handle']} | Layer: {w['layer']} | Closed: {w.get('closed')} | Length: {w.get('length')} | BoxRvt: {w['box_rvt']}")

# Save full json
with open(r"scratch\cad_selection_analyzed.json", "w", encoding="utf-8") as f:
    json.dump({"summary_type": by_type, "summary_layer": by_layer, "items": items}, f, indent=2, ensure_ascii=False)
print("\nWrote scratch\\cad_selection_analyzed.json")
