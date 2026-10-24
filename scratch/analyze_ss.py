import sys, ctypes, json
from collections import Counter
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

print(f"Doc: {doc.Name}")

DX = 132847.0
DY = 1400405.9

def analyze_ss(name, ss):
    print(f"\n--- SelectionSet: {name} (Count: {ss.Count}) ---")
    types = Counter()
    layers = Counter()
    items = []
    for i in range(ss.Count):
        try:
            ent = ss.Item(i)
            t = ent.ObjectName
            l = ent.Layer
            types[t] += 1
            layers[l] += 1
            
            item_info = {
                "idx": i,
                "type": t,
                "layer": l,
                "handle": ent.Handle
            }
            if t == "AcDbPolyline":
                coords = list(ent.Coordinates)
                pts_rvt = [[(coords[j] + DX) / 1000.0, (coords[j+1] + DY) / 1000.0] for j in range(0, len(coords), 2)]
                item_info["pts_rvt"] = pts_rvt
                item_info["closed"] = ent.Closed
                min_pt, max_pt = ent.GetBoundingBox()
                item_info["bbox_rvt"] = [
                    [(min_pt[0] + DX) / 1000.0, (min_pt[1] + DY) / 1000.0],
                    [(max_pt[0] + DX) / 1000.0, (max_pt[1] + DY) / 1000.0]
                ]
            elif t == "AcDbLine":
                sp = list(ent.StartPoint)
                ep = list(ent.EndPoint)
                item_info["start_rvt"] = [(sp[0] + DX) / 1000.0, (sp[1] + DY) / 1000.0]
                item_info["end_rvt"] = [(ep[0] + DX) / 1000.0, (ep[1] + DY) / 1000.0]
                min_pt, max_pt = ent.GetBoundingBox()
                item_info["bbox_rvt"] = [
                    [(min_pt[0] + DX) / 1000.0, (min_pt[1] + DY) / 1000.0],
                    [(max_pt[0] + DX) / 1000.0, (max_pt[1] + DY) / 1000.0]
                ]
            elif t == "AcDbBlockReference":
                ins = list(ent.InsertionPoint)
                item_info["block"] = ent.EffectiveName if hasattr(ent, "EffectiveName") else ent.Name
                item_info["ins_rvt"] = [(ins[0] + DX) / 1000.0, (ins[1] + DY) / 1000.0]
            items.append(item_info)
        except Exception as ex:
            print(f"  err item {i}: {ex}")

    print("Types:", dict(types))
    print("Layers:", dict(layers))
    return items

items_curr = analyze_ss("CURRENT", doc.ActiveSelectionSet)
items_pf = analyze_ss("PICKFIRST", doc.PickfirstSelectionSet)

with open(r"D:\Dropbox\_Documents\RevitAI\scratch\cad_ss_analysis.json", "w", encoding="utf-8") as f:
    json.dump({"current": items_curr, "pickfirst": items_pf}, f, indent=2, ensure_ascii=False)
