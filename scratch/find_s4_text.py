import sys, ctypes, json
sys.stdout.reconfigure(encoding='utf-8')
u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)
import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

DX = 132847.0
DY = 1400405.9

# Search for texts containing "S4" or window schedule in the drawing
texts = []
for i in range(doc.ModelSpace.Count):
    e = doc.ModelSpace.Item(i)
    if e.ObjectName in ["AcDbText", "AcDbMText"]:
        txt = e.TextString if e.ObjectName == "AcDbText" else e.Text
        if "S4" in txt or "s4" in txt:
            min_p, max_p = e.GetBoundingBox()
            x = (min_p[0] + DX) / 1000.0
            y = (min_p[1] + DY) / 1000.0
            texts.append({"text": txt, "pos_rvt": [x, y], "layer": e.Layer})

print(f"Found {len(texts)} texts mentioning S4:")
for t in texts:
    print(t)
