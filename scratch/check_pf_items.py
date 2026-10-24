import ctypes
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

pf = doc.PickfirstSelectionSet
print(f"Pickfirst count: {pf.Count}")
for i in range(pf.Count):
    ent = pf.Item(i)
    print(f"Item {i}: {ent.Handle} {ent.ObjectName} {ent.Layer}")
