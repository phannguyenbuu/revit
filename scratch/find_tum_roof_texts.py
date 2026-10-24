import sys, ctypes, json
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

# Let's inspect texts around (200000, -1395000) to find the title of this drawing, grid bubbles, etc.
texts = []
for ent in doc.ModelSpace:
    if ent.ObjectName in ["AcDbText", "AcDbMText"]:
        try:
            ins = ent.InsertionPoint
            if 195000 < ins[0] < 215000 and -1400000 < ins[1] < -1380000:
                txt = ent.TextString if hasattr(ent, "TextString") else ""
                texts.append((ins[0], ins[1], ent.Layer, txt))
        except:
            pass

print(f"Found {len(texts)} texts in the region:")
for x, y, lay, txt in sorted(texts, key=lambda t: t[1]):
    print(f"  ({x:.1f}, {y:.1f}) [{lay}]: {txt}")
