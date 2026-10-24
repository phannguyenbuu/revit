import sys, ctypes, json
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

DX = -113999.09
DY = 1400405.90

ent = doc.HandleToObject("4B7DA5")
coords = list(ent.Coordinates)
pts = [(coords[i], coords[i+1]) for i in range(0, len(coords), 2)]

rvt_pts = []
for p in pts:
    rx = round((p[0] + DX) / 50.0) * 50.0
    ry = round((p[1] + DY) / 50.0) * 50.0
    if not rvt_pts or rvt_pts[-1] != (rx, ry):
        rvt_pts.append((rx, ry))
if len(rvt_pts) > 1 and rvt_pts[0] == rvt_pts[-1]:
    rvt_pts.pop()

print(f"Total non-duplicate vertices: {len(rvt_pts)}")
for i, (x, y) in enumerate(rvt_pts):
    next_p = rvt_pts[(i+1)%len(rvt_pts)]
    dx = next_p[0] - x
    dy = next_p[1] - y
    is_ortho = (dx == 0 or dy == 0)
    print(f"  V{i:02d}: ({x:6.0f}, {y:6.0f}) -> next d=({dx:6.0f}, {dy:6.0f}) ortho={is_ortho}")

# Polygon Area (Shoelace formula)
area = 0.0
for i in range(len(rvt_pts)):
    j = (i + 1) % len(rvt_pts)
    area += rvt_pts[i][0] * rvt_pts[j][1]
    area -= rvt_pts[j][0] * rvt_pts[i][1]
area = abs(area) / 2.0 / 1e6
print(f"Revit Rounded Area: {area:.3f} m2 (CAD raw area was {ent.Area/1e6:.3f} m2)")

# Hole check
hole = doc.HandleToObject("44D972")
h_coords = list(hole.Coordinates)
h_pts = [(h_coords[i], h_coords[i+1]) for i in range(0, len(h_coords), 2)]
h_rvt = []
for p in h_pts:
    rx = round((p[0] + DX) / 50.0) * 50.0
    ry = round((p[1] + DY) / 50.0) * 50.0
    if not h_rvt or h_rvt[-1] != (rx, ry):
        h_rvt.append((rx, ry))
if len(h_rvt) > 1 and h_rvt[0] == h_rvt[-1]:
    h_rvt.pop()

print(f"\nHole vertices ({len(h_rvt)} vertices):")
for i, (x, y) in enumerate(h_rvt):
    print(f"  H{i:02d}: ({x:6.0f}, {y:6.0f})")

h_area = 0.0
for i in range(len(h_rvt)):
    j = (i + 1) % len(h_rvt)
    h_area += h_rvt[i][0] * h_rvt[j][1]
    h_area -= h_rvt[j][0] * h_rvt[i][1]
h_area = abs(h_area) / 2.0 / 1e6
print(f"Hole Area: {h_area:.3f} m2")
print(f"Net Area: {area - h_area:.3f} m2")
