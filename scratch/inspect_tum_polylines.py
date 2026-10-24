import sys, ctypes
sys.stdout.reconfigure(encoding='utf-8')
u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)
import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

ent_outer = doc.HandleToObject('4B7DA5')
coords_out = list(ent_outer.Coordinates)
pts_out = [(coords_out[i], coords_out[i+1]) for i in range(0, len(coords_out), 2)]

ent_hole = doc.HandleToObject('44D972')
coords_hole = list(ent_hole.Coordinates)
pts_hole = [(coords_hole[i], coords_hole[i+1]) for i in range(0, len(coords_hole), 2)]

print(f"Outer polyline 4B7DA5: {len(pts_out)} vertices, area={ent_outer.Area/1e6:.3f} m2")
for idx, p in enumerate(pts_out):
    print(f"  {idx:2d}: ({p[0]:.2f}, {p[1]:.2f})")

print(f"\nHole polyline 44D972: {len(pts_hole)} vertices, area={ent_hole.Area/1e6:.3f} m2")
for idx, p in enumerate(pts_hole):
    print(f"  {idx:2d}: ({p[0]:.2f}, {p[1]:.2f})")
