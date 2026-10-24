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

# Query entities near X in [32.0, 37.5], Y in [-0.6, 0.5]
# in CAD: X in [32000 - DX, 37500 - DX] = [-100847, -95347]
#         Y in [-600 - DY, 500 - DY] = [-1401005, -1400905]

ents = []
for i in range(doc.ModelSpace.Count):
    e = doc.ModelSpace.Item(i)
    try:
        min_p, max_p = e.GetBoundingBox()
        x1 = (min_p[0] + DX) / 1000.0
        y1 = (min_p[1] + DY) / 1000.0
        x2 = (max_p[0] + DX) / 1000.0
        y2 = (max_p[1] + DY) / 1000.0
        if x2 >= 32.0 and x1 <= 37.5 and y2 >= -0.6 and y1 <= 0.5:
            info = {
                "idx": i,
                "type": e.ObjectName,
                "layer": e.Layer,
                "handle": e.Handle,
                "bbox_rvt": [[x1, y1], [x2, y2]]
            }
            if e.ObjectName == "AcDbPolyline":
                coords = list(e.Coordinates)
                info["pts_rvt"] = [[(coords[j] + DX) / 1000.0, (coords[j+1] + DY) / 1000.0] for j in range(0, len(coords), 2)]
            elif e.ObjectName == "AcDbLine":
                sp = e.StartPoint
                ep = e.EndPoint
                info["start_rvt"] = [(sp[0] + DX) / 1000.0, (sp[1] + DY) / 1000.0]
                info["end_rvt"] = [(ep[0] + DX) / 1000.0, (ep[1] + DY) / 1000.0]
            elif e.ObjectName == "AcDbText":
                info["text"] = e.TextString
            ents.append(info)
    except:
        pass

print(f"Found {len(ents)} entities in zone")
with open(r"D:\Dropbox\_Documents\RevitAI\scratch\k1_zone_entities.json", "w", encoding="utf-8") as f:
    json.dump(ents, f, indent=2, ensure_ascii=False)
