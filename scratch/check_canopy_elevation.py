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
    if ss.Name == 'TempSS_CanopyElev':
        ss.Delete()
        break
ss = doc.SelectionSets.Add('TempSS_CanopyElev')
p1 = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [-78000.0, -1400000.0, 0.0])
p2 = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [-69000.0, -1388000.0, 0.0])
ss.Select(1, p1, p2)

print(f"Entities in canopy box: {ss.Count}")
for i in range(ss.Count):
    ent = ss.Item(i)
    if ent.ObjectName in ['AcDbText', 'AcDbMText']:
        txt = ent.TextString.strip()
        ins = list(ent.InsertionPoint)
        if any(c in txt for c in ['+', '2.', '3.', '4.', 'SÀN', 'Sàn', 'SAN', 'San', 'MÁI', 'Mái', 'MAI', 'Mai', 'SẢNH', 'Sảnh', 'SANH', 'Sanh']):
            print(f"{ent.ObjectName}: '{txt}' at ({ins[0]:.1f}, {ins[1]:.1f}) lay={ent.Layer}")
    elif ent.ObjectName == 'AcDbBlockReference':
        if ent.HasAttributes:
            for att in ent.GetAttributes():
                txt = att.TextString.strip()
                ins = list(ent.InsertionPoint)
                if any(c in txt for c in ['+', '2.', '3.', '4.', 'SÀN', 'SAN', 'MÁI', 'MAI']):
                    print(f"Block '{ent.Name}' Att {att.TagString}: '{txt}' at ({ins[0]:.1f}, {ins[1]:.1f})")
ss.Delete()
