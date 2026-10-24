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

ms = doc.ModelSpace
print(f"Doc: {doc.Name}, total ents: {ms.Count}")

ents_in_zone = []
for i in range(ms.Count):
    try:
        ent = ms.Item(i)
        p1, p2 = ent.GetBoundingBox()
        x1 = round((p1[0] + 132847.0) / 1000.0, 3)
        y1 = round((p1[1] + 1400405.9) / 1000.0, 3)
        x2 = round((p2[0] + 132847.0) / 1000.0, 3)
        y2 = round((p2[1] + 1400405.9) / 1000.0, 3)
        if 34.0 <= x2 and x1 <= 38.0 and 2.0 <= y2 and y1 <= 6.0:
            info = {
                "idx": i,
                "type": ent.ObjectName,
                "layer": ent.Layer,
                "handle": ent.Handle,
                "box": [x1, y1, x2, y2]
            }
            if "Text" in ent.ObjectName:
                info["text"] = ent.TextString
            elif ent.ObjectName == "AcDbBlockReference":
                name = ent.EffectiveName if hasattr(ent, "EffectiveName") else ent.Name
                info["block"] = name
            ents_in_zone.append(info)
    except:
        pass

print(f"Found {len(ents_in_zone)} entities in zone [34-38, 2-6]")
for e in ents_in_zone:
    if e["type"] in ["AcDbText", "AcDbMText"]:
        print(f"TEXT [{e['layer']}] {e.get('text')} at {e['box']}")
    elif e["type"] == "AcDbBlockReference":
        print(f"BLOCK [{e['layer']}] {e.get('block')} at {e['box']}")
    elif e["layer"] in ["S5", "tuong", "TUONG", "A-Wall", "A-WALL"]:
        print(f"WALL [{e['type']}] Lay:{e['layer']} Handle:{e['handle']} at {e['box']}")
