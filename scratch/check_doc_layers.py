import sys, ctypes
sys.stdout.reconfigure(encoding='utf-8')
u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

# Let's inspect layers in the document
print(f"Document: {doc.Name}")
print("Layers in doc:")
for lay in doc.Layers:
    print(f"  {lay.Name}: Freeze={lay.Freeze}, Lock={lay.Lock}, LayerOn={lay.LayerOn}")
