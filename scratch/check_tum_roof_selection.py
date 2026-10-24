import sys, ctypes, json
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

# Let's inspect the two selected items
for h in ["44DD57", "44DD52"]:
    ent = doc.HandleToObject(h)
    p1, p2 = ent.GetBoundingBox()
    coords = list(ent.Coordinates)
    pts = [(coords[i], coords[i+1]) for i in range(0, len(coords), 2)]
    print(f"\nHandle: {h}, Layer: {ent.Layer}, Area: {ent.Area/1e6:.4f} m2, Length: {ent.Length:.2f}")
    print(f"  CAD BBox: ({p1[0]:.2f}, {p1[1]:.2f}) to ({p2[0]:.2f}, {p2[1]:.2f})")
    print(f"  Width: {p2[0]-p1[0]:.2f}, Height: {p2[1]-p1[1]:.2f}")
    for idx, (x, y) in enumerate(pts):
        print(f"    V{idx}: ({x:.2f}, {y:.2f})")
