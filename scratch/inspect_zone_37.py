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

# Search entities in CAD near X_rvt in [36.0, 38.0], Y_rvt in [8.0, 12.0]
# X_cad = X_rvt * 1000 - 132847
# Y_cad = Y_rvt * 1000 - 1400405.9
# X_cad in [-96847, -94847], Y_cad in [-1392405.9, -1388405.9]

ms = doc.ModelSpace
print("Scanning near X=37.05...")
near_entities = []

# Using SelectionSets
try:
    ss = doc.SelectionSets.Item("Zone37")
    ss.Delete()
except:
    pass
ss = doc.SelectionSets.Add("Zone37")

p1 = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [-97000.0, -1393000.0, 0.0])
p2 = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [-94000.0, -1389000.0, 0.0])

ss.Select(1, p1, p2) # 1 = acSelectionSetCrossing
print(f"Entities found in zone: {ss.Count}")

for i in range(ss.Count):
    ent = ss.Item(i)
    lay = ent.Layer
    obj_name = ent.ObjectName
    b1, b2 = ent.GetBoundingBox()
    bx1 = round((b1[0] + 132847.0) / 1000.0, 3)
    by1 = round((b1[1] + 1400405.9) / 1000.0, 3)
    bx2 = round((b2[0] + 132847.0) / 1000.0, 3)
    by2 = round((b2[1] + 1400405.9) / 1000.0, 3)
    if lay in ["S5", "S4", "S3", "S2", "S1", "COT", "TBI", "Net-02"]:
        print(f"  {obj_name} | Lay: {lay} | Handle: {ent.Handle} | Box: [{bx1}, {by1}] to [{bx2}, {by2}]")

ss.Delete()
