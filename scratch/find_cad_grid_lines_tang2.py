import sys, ctypes, json
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
from win32com.client import VARIANT
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

for ss in doc.SelectionSets:
    if ss.Name == "TempSS2":
        ss.Delete()
        break

ss = doc.SelectionSets.Add("TempSS2")

# Search in box around Tang 2: X [-80000, -30000], Y [-1405000, -1380000]
p1 = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [-80000.0, -1405000.0, 0.0])
p2 = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [-30000.0, -1380000.0, 0.0])

ss.Select(1, p1, p2)

print(f"Total entities in Tang 2 box: {ss.Count}")

grid_lines = []
for i in range(ss.Count):
    ent = ss.Item(i)
    lay = ent.Layer.upper()
    if "TRUC" in lay or "TIM" in lay or "GRID" in lay:
        if ent.ObjectName == "AcDbLine":
            sp = list(ent.StartPoint)
            ep = list(ent.EndPoint)
            grid_lines.append({
                "layer": ent.Layer,
                "start": sp[:2],
                "end": ep[:2]
            })

print(f"Grid lines found in Tang 2: {len(grid_lines)}")

v_lines = set()
h_lines = set()
for g in grid_lines:
    sp = g['start']
    ep = g['end']
    if abs(sp[0] - ep[0]) < 1.0: # vertical
        v_lines.add(round(sp[0], 1))
    elif abs(sp[1] - ep[1]) < 1.0: # horizontal
        h_lines.add(round(sp[1], 1))

print("Vertical Grid X coordinates in CAD Tang 2:")
for x in sorted(v_lines):
    print(f"  X = {x}")

print("Horizontal Grid Y coordinates in CAD Tang 2:")
for y in sorted(h_lines):
    print(f"  Y = {y}")

ss.Delete()
