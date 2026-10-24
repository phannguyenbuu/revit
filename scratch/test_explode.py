import sys, ctypes
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument
blk_ref = doc.HandleToObject('497C83')

# Explode returns a tuple of new objects
exploded = blk_ref.Explode()
print(f"Exploded into {len(exploded)} objects")

exp_types = {}
boxes = []
for ent in exploded:
    t = ent.ObjectName
    exp_types[t] = exp_types.get(t, 0) + 1
    p1, p2 = ent.GetBoundingBox()
    x1 = round((p1[0] + 132847.0) / 1000.0, 4)
    y1 = round((p1[1] + 1400405.9) / 1000.0, 4)
    x2 = round((p2[0] + 132847.0) / 1000.0, 4)
    y2 = round((p2[1] + 1400405.9) / 1000.0, 4)
    w = round(abs(x2 - x1), 4)
    h = round(abs(y2 - y1), 4)
    extra = ""
    if t == "AcDbBlockReference":
        extra = f" Name: {getattr(ent, 'EffectiveName', ent.Name)}"
    boxes.append({
        "type": t,
        "layer": ent.Layer,
        "box": [x1, y1, x2, y2],
        "w": w,
        "h": h,
        "extra": extra,
        "handle": ent.Handle
    })

print("Exploded types summary:", exp_types)

# If any are still BlockReferences (like cot, cot1-2, vtretvretve), we can explode them further or get their bounding boxes!
print("\nFirst 30 exploded items:")
for i, b in enumerate(boxes[:30]):
    print(f"[{i}] {b['type']} Lay:{b['layer']} Box:{b['box']} W={b['w']*1000:.0f} H={b['h']*1000:.0f}{b['extra']}")

# Now delete the exploded temporary objects from ModelSpace so the drawing is unchanged!
for ent in exploded:
    try:
        ent.Delete()
    except:
        pass

print(f"Deleted {len(exploded)} temporary exploded objects.")
