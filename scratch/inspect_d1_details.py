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

# Search for D1 in text/schedule
print("Searching for D1 in texts across document...")
d1_texts = []
for ent in doc.ModelSpace:
    if ent.ObjectName in ["AcDbText", "AcDbMText"]:
        try:
            txt = ent.TextString
        except:
            continue
        if "D1" in txt:
            pt = ent.InsertionPoint
            x_rvt = (pt[0] + DX) / 1000.0
            y_rvt = (pt[1] + DY) / 1000.0
            d1_texts.append({"handle": ent.Handle, "text": txt, "pos_rvt": [x_rvt, y_rvt], "layer": ent.Layer})

print(f"Found {len(d1_texts)} texts with 'D1':")
for t in d1_texts[:10]:
    print(t)

# Find entities around X in [0.0, 1.0], Y in [4.0, 9.5]
print("\nSearching entities in Trục 1 wall zone (X in [0.0, 1.0], Y in [4.0, 9.5])...")
zone_ents = []
for ent in doc.ModelSpace:
    try:
        min_pt, max_pt = ent.GetBoundingBox()
        x1 = (min_pt[0] + DX) / 1000.0
        y1 = (min_pt[1] + DY) / 1000.0
        x2 = (max_pt[0] + DX) / 1000.0
        y2 = (max_pt[1] + DY) / 1000.0
        
        if -0.5 <= x1 <= 1.5 and 4.0 <= y1 <= 9.5:
            info = {
                "handle": ent.Handle,
                "type": ent.ObjectName,
                "layer": ent.Layer,
                "bbox_rvt": [[round(x1, 3), round(y1, 3)], [round(x2, 3), round(y2, 3)]]
            }
            if ent.ObjectName == "AcDbText":
                info["text"] = ent.TextString
            zone_ents.append(info)
    except:
        pass

print(f"Found {len(zone_ents)} entities in zone:")
for e in zone_ents:
    print(e)
