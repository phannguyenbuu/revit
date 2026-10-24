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
    if ss.Name == 'TempSS_Tang3':
        ss.Delete()
        break
ss = doc.SelectionSets.Add('TempSS_Tang3')
p1 = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [-15000.0, -1406000.0, 0.0])
p2 = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [32000.0, -1380000.0, 0.0])
ss.Select(1, p1, p2)

print(f"Entities found in Tang 3 area: {ss.Count}")
grid_bubbles = []
for i in range(ss.Count):
    ent = ss.Item(i)
    if ent.ObjectName == 'AcDbBlockReference' and 'TRUC' in ent.Name.upper():
        if ent.HasAttributes:
            for att in ent.GetAttributes():
                txt = att.TextString.strip()
                ins = list(ent.InsertionPoint)
                grid_bubbles.append((txt, ins[0], ins[1], att.TagString))

for txt, x, y, tag in sorted(grid_bubbles, key=lambda item: item[1]):
    print(f"Grid Bubble: '{txt}' at ({x:9.1f}, {y:10.1f}) tag={tag}")
ss.Delete()
