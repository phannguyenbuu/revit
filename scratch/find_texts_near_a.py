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

ms = doc.ModelSpace
print(f"Scanning ModelSpace ({ms.Count} entities)...")

texts_near_a = []
for i in range(ms.Count):
    ent = ms.Item(i)
    name = ent.ObjectName
    if "Text" in name:
        try:
            p = ent.InsertionPoint
            rvt_x = round((p[0] + 132847.0) / 1000.0, 3)
            rvt_y = round((p[1] + 1400405.9) / 1000.0, 3)
            if -3.0 <= rvt_y <= 3.0 and -2.0 <= rvt_x <= 40.0:
                texts_near_a.append({
                    "text": ent.TextString,
                    "layer": ent.Layer,
                    "rvt_x": rvt_x,
                    "rvt_y": rvt_y
                })
        except:
            pass

texts_near_a.sort(key=lambda t: t["rvt_x"])
print(f"Found {len(texts_near_a)} texts near Trục A:")
for t in texts_near_a:
    print(f"  X={t['rvt_x']:.2f}, Y={t['rvt_y']:.2f} | Layer: {t['layer']} | '{t['text']}'")
