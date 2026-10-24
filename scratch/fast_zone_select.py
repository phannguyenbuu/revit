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

# Let's select by crossing window in AutoCAD COM
# In CAD coords:
# X_cad = X_rvt * 1000 - 132847.0
# Y_cad = Y_rvt * 1000 - 1400405.9
def rvt_to_cad(x, y):
    return (x * 1000.0 - 132847.0, y * 1000.0 - 1400405.9)

p1 = rvt_to_cad(34.0, 2.0)
p2 = rvt_to_cad(38.0, 6.0)

import win32com.client.util
import array

# Use SelectByPolygon or Select with crossing window
ss = None
try:
    ss = doc.SelectionSets.Item("TempSS")
    ss.Delete()
except:
    pass
ss = doc.SelectionSets.Add("TempSS")

pt1 = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [p1[0], p1[1], 0.0])
pt2 = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [p2[0], p2[1], 0.0])

# 1 = acSelectionSetWindow, 2 = acSelectionSetCrossing
ss.Select(1, pt1, pt2) # Crossing
if ss.Count == 0:
    ss.Select(2, pt1, pt2)

print(f"Entities in window [34-38, 2-6]: {ss.Count}")
for i in range(ss.Count):
    ent = ss.Item(i)
    minp, maxp = ent.GetBoundingBox()
    x1 = round((minp[0] + 132847.0) / 1000.0, 3)
    y1 = round((minp[1] + 1400405.9) / 1000.0, 3)
    x2 = round((maxp[0] + 132847.0) / 1000.0, 3)
    y2 = round((maxp[1] + 1400405.9) / 1000.0, 3)
    t = ""
    if "Text" in ent.ObjectName:
        t = f" text='{ent.TextString}'"
    elif ent.ObjectName == "AcDbBlockReference":
        name = ent.EffectiveName if hasattr(ent, "EffectiveName") else ent.Name
        t = f" block='{name}'"
    print(f"[{i}] {ent.ObjectName} lay={ent.Layer} handle={ent.Handle} box=[{x1}, {y1}, {x2}, {y2}]{t}")

ss.Delete()
