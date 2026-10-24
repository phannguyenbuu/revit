import sys, ctypes
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
    if ss.Name == 'TempSS_Col':
        ss.Delete()
        break
ss = doc.SelectionSets.Add('TempSS_Col')
p1 = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [-75000.0, -1402000.0, 0.0])
p2 = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [-65000.0, -1398000.0, 0.0])
ss.Select(1, p1, p2)

print(f"Entities found: {ss.Count}")
for i in range(ss.Count):
    ent = ss.Item(i)
    if 'COT' in ent.Layer.upper():
        name = getattr(ent, 'Name', '')
        ins = list(ent.InsertionPoint)
        print(f"{ent.ObjectName} '{name}' at ({ins[0]:.1f}, {ins[1]:.1f}) layer={ent.Layer}")
ss.Delete()
