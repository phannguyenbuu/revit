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

unique_pts = []
for p in pts_out:
    if not unique_pts or (abs(p[0] - unique_pts[-1][0]) > 1.0 or abs(p[1] - unique_pts[-1][1]) > 1.0):
        unique_pts.append(p)

if unique_pts and (abs(unique_pts[0][0] - unique_pts[-1][0]) < 1.0 and abs(unique_pts[0][1] - unique_pts[-1][1]) < 1.0):
    unique_pts = unique_pts[:-1]

dx = -113999.09
dy = 1400405.90

print(f"Unique outer vertices count: {len(unique_pts)}")
print(f"{'Idx':3s} | {'CAD X':10s} {'CAD Y':12s} | {'Revit X':10s} {'Revit Y':10s} | {'Round50 X':10s} {'Round50 Y':10s}")
print("-" * 75)

revit_outer = []
for i, (xc, yc) in enumerate(unique_pts):
    xr = xc + dx
    yr = yc + dy
    xr_50 = round(xr / 50.0) * 50.0
    yr_50 = round(yr / 50.0) * 50.0
    # align east wall 37275 -> 37250
    if abs(xr_50 - 37300.0) < 1.0 and xr > 37200:
        xr_50 = 37250.0
    print(f"{i:3d} | {xc:10.2f} {yc:12.2f} | {xr:10.2f} {yr:10.2f} | {xr_50:10.1f} {yr_50:10.1f}")
    revit_outer.append((xr_50, yr_50))

def poly_area(p):
    return sum(p[i][0]*p[(i+1)%len(p)][1] - p[(i+1)%len(p)][0]*p[i][1] for i in range(len(p))) / 2.0

print(f"\nOuter Signed Area: {poly_area(revit_outer)/1e6:.3f} m2")
for i in range(len(revit_outer)):
    j = (i + 1) % len(revit_outer)
    p0, p1 = revit_outer[i], revit_outer[j]
    dx_e = p1[0] - p0[0]
    dy_e = p1[1] - p0[1]
    length = (dx_e**2 + dy_e**2)**0.5
    print(f"Edge {i:2d}->{j:2d}: ({p0[0]:6.0f}, {p0[1]:6.0f}) -> ({p1[0]:6.0f}, {p1[1]:6.0f}) | Len={length:6.0f} mm, Ortho={(dx_e==0 or dy_e==0)}")
