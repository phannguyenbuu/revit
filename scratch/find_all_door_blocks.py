import sys, ctypes
sys.stdout.reconfigure(encoding='utf-8')
u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

DX = 70950.0
DY = 1400406.0

ss = doc.PickfirstSelectionSet if doc.PickfirstSelectionSet.Count > 0 else doc.ActiveSelectionSet

print(f"Scanning selection of {ss.Count} items for doors...")
doors = []
for i in range(ss.Count):
    ent = ss.Item(i)
    lay = ent.Layer
    if lay in ('32-CUA', 'A-Door') and ent.ObjectName == 'AcDbBlockReference':
        p1, p2 = ent.GetBoundingBox()
        min_x = (p1[0] + DX) / 1000.0
        max_x = (p2[0] + DX) / 1000.0
        min_y = (p1[1] + DY) / 1000.0
        max_y = (p2[1] + DY) / 1000.0
        cx = (min_x + max_x) / 2.0
        cy = (min_y + max_y) / 2.0
        w = max_x - min_x
        h = max_y - min_y
        name = getattr(ent, 'EffectiveName', ent.Name)
        doors.append({
            'handle': ent.Handle,
            'name': name,
            'layer': lay,
            'center': (round(cx, 3), round(cy, 3)),
            'size': (round(w, 3), round(h, 3)),
            'rot': ent.Rotation
        })

print(f"Total door blocks found: {len(doors)}")
doors.sort(key=lambda d: (round(d['center'][1], 1), round(d['center'][0], 1)))
for i, d in enumerate(doors):
    print(f"  [{i+1}] Handle={d['handle']} Name={d['name']} Lay={d['layer']}: center=({d['center'][0]:.2f}, {d['center'][1]:.2f}), size=({d['size'][0]:.2f}m x {d['size'][1]:.2f}m), rot={d['rot']:.2f}")
