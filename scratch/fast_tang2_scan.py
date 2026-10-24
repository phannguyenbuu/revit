import sys, ctypes
sys.stdout.reconfigure(encoding='utf-8')
u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

# Remove existing selection set if exists
for ss_old in doc.SelectionSets:
    if ss_old.Name == "TempTang2":
        ss_old.Delete()
        break

ss = doc.SelectionSets.Add("TempTang2")

# Points for crossing window: min_x = -72000, min_y = -1402000, max_x = -32000, max_y = -1384000
pt1 = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [-72000.0, -1402000.0, 0.0])
pt2 = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [-32000.0, -1384000.0, 0.0])

# 1 = acSelectionSetCrossing
ss.Select(1, pt1, pt2)
print(f"Total entities in Tầng 2 crossing: {ss.Count}")

layers = {}
wall_ents = []
for i in range(ss.Count):
    ent = ss.Item(i)
    lay = ent.Layer
    layers[lay] = layers.get(lay, 0) + 1
    if 'tuong' in lay.lower() or 'wall' in lay.lower() or lay in ('TUONG', 'Tuong-0.5', 'A-Wall', 'A_Walls', 'NET CAT', 'BETONG', 'Net-02'):
        wall_ents.append((ent.Handle, lay, ent.ObjectName))

for lay, c in sorted(layers.items(), key=lambda x: -x[1]):
    print(f"  {lay}: {c}")

print(f"\nWall entities count: {len(wall_ents)}")

ss.Delete()
