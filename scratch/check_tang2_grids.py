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
    if ss.Name == 'TempSS_Text':
        ss.Delete()
        break
ss = doc.SelectionSets.Add('TempSS_Text')
# search in broader area around Tang 2
p1 = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [-85000.0, -1410000.0, 0.0])
p2 = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [-25000.0, -1375000.0, 0.0])
ss.Select(1, p1, p2)

print(f"Entities found: {ss.Count}")
for i in range(ss.Count):
    ent = ss.Item(i)
    if ent.ObjectName in ['AcDbText', 'AcDbMText']:
        ins = list(ent.InsertionPoint)
        txt = ent.TextString.strip()
        if len(txt) < 30:
            print(f"{ent.ObjectName}: text='{txt}', at=({ins[0]:.1f}, {ins[1]:.1f}) lay={ent.Layer}")
    elif ent.ObjectName == 'AcDbBlockReference':
        if ent.HasAttributes:
            for att in ent.GetAttributes():
                txt = att.TextString.strip()
                ins = list(ent.InsertionPoint)
                print(f"Block '{ent.Name}' Att: tag='{att.TagString}', text='{txt}', at=({ins[0]:.1f}, {ins[1]:.1f})")
ss.Delete()
