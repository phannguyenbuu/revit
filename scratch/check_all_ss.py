import sys, ctypes, time, json
sys.stdout.reconfigure(encoding='utf-8')

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

print(f"Doc: {doc.Name}")
print(f"PickfirstSelectionSet: {doc.PickfirstSelectionSet.Count}")
try:
    print(f"ActiveSelectionSet: {doc.ActiveSelectionSet.Count}")
except Exception as e:
    print(f"ActiveSelectionSet err: {e}")

print("All SelectionSets in document:")
for i in range(doc.SelectionSets.Count):
    ss = doc.SelectionSets.Item(i)
    print(f"  SS[{i}] Name: '{ss.Name}', Count: {ss.Count}")
