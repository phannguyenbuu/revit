import sys, ctypes, json
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

def to_rvt(x, y):
    return (x + 70950.0) / 1000.0, (y + 1400406.0) / 1000.0

# Check text near WC
ms = doc.ModelSpace
texts = []
for i in range(ms.Count):
    ent = ms.Item(i)
    if 'Text' in ent.ObjectName:
        ins = ent.InsertionPoint
        rx, ry = to_rvt(ins[0], ins[1])
        if 32.0 <= rx <= 37.0 and 7.5 <= ry <= 10.5:
            texts.append({"text": ent.TextString, "pos": [round(rx, 3), round(ry, 3)], "layer": ent.Layer})

print("Texts in WC area:")
for t in texts:
    print(t)
