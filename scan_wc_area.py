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

def to_cad(rx, ry):
    return rx * 1000.0 - 70950.0, ry * 1000.0 - 1400406.0

# Search entities in ModelSpace around WC: X_rvt in [33, 37], Y_rvt in [7.5, 10.5]
c_min = to_cad(33.0, 7.5)
c_max = to_cad(37.0, 10.5)

print(f"Scanning CAD ModelSpace for WC elements...")
wc_ents = []
ms = doc.ModelSpace
for i in range(ms.Count):
    ent = ms.Item(i)
    try:
        p1, p2 = ent.GetBoundingBox()
        # check overlap
        if p2[0] < c_min[0] or p1[0] > c_max[0] or p2[1] < c_min[1] or p1[1] > c_max[1]:
            continue
        
        rx1, ry1 = to_rvt(p1[0], p1[1])
        rx2, ry2 = to_rvt(p2[0], p2[1])
        
        obj = {
            "handle": ent.Handle,
            "type": ent.ObjectName,
            "layer": ent.Layer,
            "rvt_box": [round(rx1, 3), round(ry1, 3), round(rx2, 3), round(ry2, 3)]
        }
        if ent.ObjectName == "AcDbLine":
            sp = to_rvt(ent.StartPoint[0], ent.StartPoint[1])
            ep = to_rvt(ent.EndPoint[0], ent.EndPoint[1])
            obj["line"] = [round(sp[0], 3), round(sp[1], 3), round(ep[0], 3), round(ep[1], 3)]
        elif "Polyline" in ent.ObjectName:
            coords = list(ent.Coordinates)
            pts = [to_rvt(coords[j], coords[j+1]) for j in range(0, len(coords), 2)]
            obj["poly"] = [[round(p[0], 3), round(p[1], 3)] for p in pts]
            obj["closed"] = ent.Closed
        elif "Text" in ent.ObjectName:
            obj["text"] = ent.TextString
            ins = to_rvt(ent.InsertionPoint[0], ent.InsertionPoint[1])
            obj["ins"] = [round(ins[0], 3), round(ins[1], 3)]
            
        wc_ents.append(obj)
    except:
        pass

print(f"Found {len(wc_ents)} entities in WC area")
with open(r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\wc_all_cad_ents.json", "w", encoding="utf-8") as f:
    json.dump(wc_ents, f, indent=2, ensure_ascii=False)

# Filter S5 entities
s5_ents = [e for e in wc_ents if e['layer'] == 'S5']
print(f"S5 entities in WC area: {len(s5_ents)}")
for e in s5_ents:
    print(e)
