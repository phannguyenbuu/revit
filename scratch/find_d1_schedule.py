import ctypes
u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client

pythoncom.CoInitialize()
acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = None
for i in range(acad.Documents.Count):
    d = acad.Documents.Item(i)
    if 'LONG TIÊN' in d.Name:
        doc = d
        break
if not doc:
    doc = acad.ActiveDocument

DX = 132847.0
DY = 1400405.9

# Search for D1 in texts and surrounding texts in schedule
for ent in doc.ModelSpace:
    if ent.ObjectName in ["AcDbText", "AcDbMText"]:
        try:
            txt = ent.TextString
            if txt.strip() == "D1" or txt.strip() == "Đ1":
                pt = ent.InsertionPoint
                print(f"Found '{txt}' at CAD: ({pt[0]:.1f}, {pt[1]:.1f}), RVT: ({(pt[0]+DX)/1000.0:.2f}, {(pt[1]+DY)/1000.0:.2f})")
        except:
            pass
