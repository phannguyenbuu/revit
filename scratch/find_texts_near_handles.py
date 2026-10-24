import sys, ctypes, json
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

DX = 132847.0
DY = 1400405.9

with open(r"D:\Dropbox\_Documents\RevitAI\scratch\handles_21_dump.json", "r", encoding="utf-8") as f:
    items = json.load(f)

# Find all texts in the model space
texts = []
for ent in doc.ModelSpace:
    try:
        oname = ent.ObjectName
        if oname in ("AcDbText", "AcDbMText"):
            ip = ent.InsertionPoint
            x_rvt = (ip[0] + DX) / 1000.0
            y_rvt = (ip[1] + DY) / 1000.0
            txt = ent.TextString if hasattr(ent, "TextString") else ent.Text
            # filter to relevant zone: X in [-2, 35], Y in [-2, 16]
            if -2 <= x_rvt <= 35 and -2 <= y_rvt <= 16:
                texts.append({"text": txt, "x": x_rvt, "y": y_rvt})
    except Exception:
        pass

print(f"Collected {len(texts)} texts in the zone")

# For each item, find nearby texts
for i, it in enumerate(items):
    bx = it['bbox_rvt']
    cx = (bx['min'][0] + bx['max'][0]) / 2.0
    cy = (bx['min'][1] + bx['max'][1]) / 2.0
    
    nearby = []
    for t in texts:
        dist = ((t['x'] - cx)**2 + (t['y'] - cy)**2)**0.5
        if dist < 2.0:
            nearby.append(f"'{t['text']}'(d={dist:.2f})")
    
    print(f"[{i:2d}] {it['handle']} at ({cx:.2f}, {cy:.2f}): " + ", ".join(nearby[:5]))
