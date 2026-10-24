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

selected = []
if pf.Count > 0:
    for i in range(pf.Count):
        selected.append(pf.Item(i))
else:
    act = doc.ActiveSelectionSet
    print(f"ActiveSelectionSet count: {act.Count}")
    for i in range(act.Count):
        selected.append(act.Item(i))

print(f"Total selected items: {len(selected)}")

for idx, ent in enumerate(selected):
    print(f"\n--- Item {idx}: Handle={ent.Handle}, ObjectName={ent.ObjectName}, Layer={ent.Layer} ---")
    p1, p2 = ent.GetBoundingBox()
    print(f"  CAD BBox: ({p1[0]:.2f}, {p1[1]:.2f}) to ({p2[0]:.2f}, {p2[1]:.2f})")
    
    if hasattr(ent, "Area"):
        print(f"  CAD Area: {ent.Area/1e6:.4f} m2")
    if hasattr(ent, "Length"):
        print(f"  CAD Length: {ent.Length:.2f} mm")
    if hasattr(ent, "Closed"):
        print(f"  Closed: {ent.Closed}")
    if "Polyline" in ent.ObjectName:
        coords = list(ent.Coordinates)
        pts = [(coords[j], coords[j+1]) for j in range(0, len(coords), 2)]
        print(f"  Vertices count: {len(pts)}")
        for vidx, (vx, vy) in enumerate(pts):
            print(f"    V{vidx}: ({vx:.2f}, {vy:.2f})")
