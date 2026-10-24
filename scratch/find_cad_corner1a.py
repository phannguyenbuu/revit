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

# Remove existing temp selection set if exists
for ss in doc.SelectionSets:
    if ss.Name == "TempSS":
        ss.Delete()
        break

ss = doc.SelectionSets.Add("TempSS")

# Corner (1, A) in CAD is near X = -132397, Y = -1400506
p1 = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [-133000.0, -1401000.0, 0.0])
p2 = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [-131500.0, -1399500.0, 0.0])

# acSelectionSetCrossing = 1
ss.Select(1, p1, p2)

print(f"Entities found near Corner (1,A): {ss.Count}")
for i in range(ss.Count):
    ent = ss.Item(i)
    name = ent.ObjectName
    layer = ent.Layer
    extra = ""
    if name == "AcDbBlockReference":
        extra = f"Block: {ent.Name}, Ins: {list(ent.InsertionPoint)}"
    elif name == "AcDbText":
        extra = f"Text: '{ent.TextString}', Ins: {list(ent.InsertionPoint)}"
    elif name == "AcDbLine":
        extra = f"Line: {list(ent.StartPoint)[:2]} -> {list(ent.EndPoint)[:2]}"
    print(f"  [{i}] {name} on {layer} | {extra}")

ss.Delete()
