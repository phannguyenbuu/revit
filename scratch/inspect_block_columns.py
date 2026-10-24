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

blk_ref = doc.HandleToObject('497C83')
print(f"BlockRef Name: {blk_ref.Name}, EffectiveName: {getattr(blk_ref, 'EffectiveName', '')}")
ins = blk_ref.InsertionPoint
print(f"InsertionPoint CAD: {ins[0]}, {ins[1]}, {ins[2]}")
x_scale = blk_ref.XScaleFactor
y_scale = blk_ref.YScaleFactor
z_scale = blk_ref.ZScaleFactor
rot = blk_ref.Rotation
print(f"Scale: ({x_scale}, {y_scale}, {z_scale}), Rotation: {rot}")

# Convert insertion point to Revit coordinates
x_ins_rvt = (ins[0] + 132847.0) / 1000.0
y_ins_rvt = (ins[1] + 1400405.9) / 1000.0
print(f"InsertionPoint RVT: ({x_ins_rvt}, {y_ins_rvt})")

# Look up block definition in doc.Blocks
bdef = doc.Blocks.Item(blk_ref.Name)
print(f"Block definition entity count: {bdef.Count}")

ents_summary = {}
ents_list = []

for i in range(bdef.Count):
    ent = bdef.Item(i)
    t = ent.ObjectName
    ents_summary[t] = ents_summary.get(t, 0) + 1
    
    ent_info = {
        "idx": i,
        "type": t,
        "layer": ent.Layer,
        "handle": ent.Handle
    }
    
    try:
        p1, p2 = ent.GetBoundingBox()
        ent_info["box_local"] = [p1[0], p1[1], p2[0], p2[1]]
    except:
        pass
        
    if "Polyline" in t:
        coords = list(ent.Coordinates)
        pts = [(coords[j], coords[j+1]) for j in range(0, len(coords), 2)]
        ent_info["closed"] = ent.Closed
        ent_info["pts_count"] = len(pts)
        ent_info["pts"] = pts
    elif t == "AcDbLine":
        ent_info["start"] = list(ent.StartPoint)
        ent_info["end"] = list(ent.EndPoint)
    
    ents_list.append(ent_info)

print("Entities summary in block:", ents_summary)

with open(r"scratch\block_columns_entities.json", "w", encoding="utf-8") as f:
    json.dump({
        "insertion_point_cad": list(ins),
        "scale": [x_scale, y_scale, z_scale],
        "rotation": rot,
        "entities": ents_list
    }, f, indent=2, ensure_ascii=False)

print("Saved entities to scratch\\block_columns_entities.json")
