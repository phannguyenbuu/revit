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
    print(f"ActiveSelectionSet count: {act.Count}")
    for i in range(act.Count):
        selected.append(act.Item(i))

print(f"Total items: {len(selected)}")

items = []
for idx, ent in enumerate(selected):
    obj_name = ent.ObjectName
    layer = ent.Layer
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
        ip = ent.InsertionPoint
        item_info["ins_rvt"] = [
            round((ip[0] + 132847.0) / 1000.0, 4),
            round((ip[1] + 1400405.9) / 1000.0, 4),
            round(ip[2] / 1000.0, 4)
        ]
        item_info["rotation"] = ent.Rotation
        if ent.HasAttributes:
            item_info["attrs"] = {att.TagString: att.TextString for att in ent.GetAttributes()}
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
    elif obj_name == "AcDbLine":
        sp = ent.StartPoint
        ep = ent.EndPoint
        item_info["start_rvt"] = [
            round((sp[0] + 132847.0) / 1000.0, 4),
            round((sp[1] + 1400405.9) / 1000.0, 4)
        ]
        item_info["end_rvt"] = [
            round((ep[0] + 132847.0) / 1000.0, 4),
            round((ep[1] + 1400405.9) / 1000.0, 4)
        ]
        item_info["length"] = round(ent.Length, 3)

    items.append(item_info)

with open(r"scratch\cad_selection_d5.json", "w", encoding="utf-8") as f:
    json.dump(items, f, indent=2, ensure_ascii=False)

print(f"Dumped {len(items)} items to scratch\\cad_selection_d5.json")
for it in items:
    print(f"[{it['idx']}] {it['type']} | Layer: {it['layer']} | Handle: {it['handle']} | BoxRVT: {it['box_rvt']}")
    if "block_name" in it:
        print(f"     Block: {it['block_name']} | Ins: {it.get('ins_rvt')} | Attrs: {it.get('attrs')}")
    if "text" in it:
        print(f"     Text: '{it['text']}'")
    if "pts_rvt" in it:
        print(f"     Pts: {it['pts_rvt']}")
    if "start_rvt" in it:
        print(f"     Line: {it['start_rvt']} -> {it['end_rvt']}")
