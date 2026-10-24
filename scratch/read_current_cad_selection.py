import sys, ctypes, json
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
act = doc.ActiveSelectionSet
print(f"ActiveSS count: {act.Count}")

ss = pf if pf.Count > 0 else act
print(f"Using selection set with count: {ss.Count}")

DX = 132847.0
DY = 1400405.9

items = []
for i in range(ss.Count):
    ent = ss.Item(i)
    obj_name = ent.ObjectName
    layer = ent.Layer
    handle = ent.Handle
    
    info = {
        "index": i,
        "type": obj_name,
        "layer": layer,
        "handle": handle
    }
    
    try:
        min_pt, max_pt = ent.GetBoundingBox()
        info["bbox_cad"] = {"min": [min_pt[0], min_pt[1]], "max": [max_pt[0], max_pt[1]]}
        info["bbox_rvt"] = {
            "min": [(min_pt[0] + DX) / 1000.0, (min_pt[1] + DY) / 1000.0],
            "max": [(max_pt[0] + DX) / 1000.0, (max_pt[1] + DY) / 1000.0]
        }
    except Exception as e:
        info["bbox_err"] = str(e)

    if obj_name == "AcDbPolyline":
        coords = list(ent.Coordinates)
        pts_cad = []
        pts_rvt = []
        for j in range(0, len(coords), 2):
            x = coords[j]
            y = coords[j+1]
            pts_cad.append([x, y])
            pts_rvt.append([(x + DX) / 1000.0, (y + DY) / 1000.0])
        info["points_cad"] = pts_cad
        info["points_rvt"] = pts_rvt
        info["closed"] = ent.Closed

    elif obj_name == "AcDbLine":
        sp = list(ent.StartPoint)
        ep = list(ent.EndPoint)
        info["start_cad"] = sp
        info["end_cad"] = ep
        info["start_rvt"] = [(sp[0] + DX) / 1000.0, (sp[1] + DY) / 1000.0]
        info["end_rvt"] = [(ep[0] + DX) / 1000.0, (ep[1] + DY) / 1000.0]

    elif obj_name == "AcDbBlockReference":
        ins = list(ent.InsertionPoint)
        bname = ent.EffectiveName if hasattr(ent, "EffectiveName") else ent.Name
        info["block_name"] = bname
        info["ins_cad"] = ins
        info["ins_rvt"] = [(ins[0] + DX) / 1000.0, (ins[1] + DY) / 1000.0]

    elif obj_name == "AcDbText":
        info["text"] = ent.TextString

    elif obj_name == "AcDbMText":
        info["text"] = ent.Text

    items.append(info)

out_file = r"D:\Dropbox\_Documents\RevitAI\scratch\current_cad_selection.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(items, f, indent=2, ensure_ascii=False)

print(f"Dumped {len(items)} items to {out_file}")
