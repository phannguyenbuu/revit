import sys, ctypes
sys.stdout.reconfigure(encoding='utf-8')
u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)
import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument
print('Doc:', doc.Name)
print('doc.SelectionSets.Count:', doc.SelectionSets.Count)
for i in range(doc.SelectionSets.Count):
    ss = doc.SelectionSets.Item(i)
    print(f'SS[{i}]: Name="{ss.Name}", Count={ss.Count}')
