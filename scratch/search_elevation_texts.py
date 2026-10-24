import sys, ctypes
sys.stdout.reconfigure(encoding='utf-8')
u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)
import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

msp = doc.ModelSpace
print(f"Searching {msp.Count} entities in ModelSpace...")
found = []
for i in range(msp.Count):
    ent = msp.Item(i)
    txt = ""
    if ent.ObjectName in ['AcDbText', 'AcDbMText']:
        txt = ent.TextString
    elif ent.ObjectName == 'AcDbBlockReference' and ent.HasAttributes:
        for att in ent.GetAttributes():
            txt += " " + att.TextString
    
    if any(k in txt for k in ['2.40', '3.40', '2400', '3400', '+2.4', '+3.4', '+3,4', '+2,4', '2.4', '3.4']):
        ins = getattr(ent, 'InsertionPoint', (0,0,0))
        found.append((txt.strip(), ins[0], ins[1], ent.Layer))

print(f"Found {len(found)} matches:")
for t, x, y, lay in found[:40]:
    print(f"  '{t}' at ({x:.1f}, {y:.1f}) layer={lay}")
