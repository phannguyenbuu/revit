import ctypes
u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client, json

pythoncom.CoInitialize()
acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = None
for d in acad.Documents:
    if 'LONG TIÊN' in d.Name:
        doc = d
        break
if not doc:
    doc = acad.ActiveDocument

DX = 132847.0
DY = 1400405.9

# Check entities by handle
for h in ["44C233", "44C244", "44C201", "44C200"]:
    ent = doc.HandleToObject(h)
    print(f"Handle {h}: ObjectName={ent.ObjectName}, Layer={ent.Layer}, Color={ent.Color}")
    if ent.ObjectName == "AcDbPolyline":
        coords = list(ent.Coordinates)
        pts = []
        for i in range(0, len(coords), 2):
            pts.append([(coords[i] + DX)/1000.0, (coords[i+1] + DY)/1000.0])
        print(f"  Pts RVT: {pts}")

# Check any other entities selected or nearby
print("\nActive selection set handles:")
for i in range(doc.ActiveSelectionSet.Count):
    ent = doc.ActiveSelectionSet.Item(i)
    print(f"  {ent.Handle} {ent.ObjectName} {ent.Layer}")

print("\nPickfirst selection set handles:")
for i in range(doc.PickfirstSelectionSet.Count):
    ent = doc.PickfirstSelectionSet.Item(i)
    print(f"  {ent.Handle} {ent.ObjectName} {ent.Layer}")
