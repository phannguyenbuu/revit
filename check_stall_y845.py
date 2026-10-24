import sys, ctypes, json
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

def to_rvt(x, y):
    return (x + 70950.0) / 1000.0, (y + 1400406.0) / 1000.0

# Search entities in selection first
# The selection had 52 entities.
# Are there other entities in ModelSpace near (35.0, 8.45)?
ms = doc.ModelSpace
found = []
for i in range(ms.Count):
    ent = ms.Item(i)
    if ent.Layer == 'S5':
        p1, p2 = ent.GetBoundingBox()
        rx1, ry1 = to_rvt(p1[0], p1[1])
        rx2, ry2 = to_rvt(p2[0], p2[1])
        if rx2 >= 34.0 and rx1 <= 37.0 and ry2 >= 7.5 and ry1 <= 10.0:
            found.append({
                "handle": ent.Handle,
                "type": ent.ObjectName,
                "b1": [round(rx1, 4), round(ry1, 4)],
                "b2": [round(rx2, 4), round(ry2, 4)]
            })

print(f"Total S5 in WC: {len(found)}")
for f in found:
    print(f)
