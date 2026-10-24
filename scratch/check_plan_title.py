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
    if ss.Name == 'TempSS_PlanTitle':
        ss.Delete()
        break
ss = doc.SelectionSets.Add('TempSS_PlanTitle')
p1 = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [110000.0, -1415000.0, 0.0])
p2 = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [160000.0, -1380000.0, 0.0])
ss.Select(1, p1, p2)

print(f"Entities found: {ss.Count}")
titles = []
for i in range(ss.Count):
    ent = ss.Item(i)
    if ent.ObjectName in ['AcDbText', 'AcDbMText']:
        txt = ent.TextString.strip()
        ins = list(ent.InsertionPoint)
        if any(w in txt.upper() for w in ['MẶT BẰNG', 'MAT BANG', 'TẦNG', 'TANG', 'MÁI', 'MAI', 'ÁP MÁI', 'AP MAI']):
            titles.append((txt, ins[0], ins[1], ent.Layer))

for t, x, y, lay in sorted(titles, key=lambda it: it[2]):
    print(f"Title: '{t}' at ({x:.1f}, {y:.1f}) layer={lay}")
ss.Delete()
