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

bdef = doc.Blocks.Item('columns')
nested = []
for i in range(bdef.Count):
    ent = bdef.Item(i)
    if ent.ObjectName == 'AcDbBlockReference':
        name = getattr(ent, 'EffectiveName', ent.Name)
        ins = ent.InsertionPoint
        x_cad = -132297.0075576764 + ins[0]
        y_cad = -1387205.8955601 + ins[1]
        x_rvt = round((x_cad + 132847.0) / 1000.0, 4)
        y_rvt = round((y_cad + 1400405.9) / 1000.0, 4)
        p1, p2 = ent.GetBoundingBox()
        x1_rvt = round((-132297.0075576764 + p1[0] + 132847.0) / 1000.0, 4)
        y1_rvt = round((-1387205.8955601 + p1[1] + 1400405.9) / 1000.0, 4)
        x2_rvt = round((-132297.0075576764 + p2[0] + 132847.0) / 1000.0, 4)
        y2_rvt = round((-1387205.8955601 + p2[1] + 1400405.9) / 1000.0, 4)
        w = round(abs(x2_rvt - x1_rvt), 4)
        h = round(abs(y2_rvt - y1_rvt), 4)
        nested.append({
            "idx": i,
            "name": name,
            "layer": ent.Layer,
            "handle": ent.Handle,
            "ins": [x_rvt, y_rvt],
            "box": [x1_rvt, y1_rvt, x2_rvt, y2_rvt],
            "w": w,
            "h": h
        })

print(f"Total nested blocks: {len(nested)}")
for n in nested:
    print(f"[{n['idx']}] Name:{n['name']} Lay:{n['layer']} Ins:({n['ins'][0]}, {n['ins'][1]}) Box:[{n['box'][0]}, {n['box'][1]}, {n['box'][2]}, {n['box'][3]}] W={n['w']*1000:.0f} H={n['h']*1000:.0f}")

with open(r"scratch\nested_blocks.json", "w", encoding="utf-8") as f:
    json.dump(nested, f, indent=2)
