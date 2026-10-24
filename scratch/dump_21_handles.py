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

print(f"Connected to CAD Document: {doc.Name}")

handles = [
    "44C2D2",
    "44C64C",
    "44C80F",
    "44C802",
    "44C7EF",
    "44C81C",
    "44C81E",
    "44C7F5",
    "44C707",
    "44C71B",
    "44C71C",
    "44C6F5",
    "44C766",
    "44C768",
    "44C705",
    "44C73D",
    "44C74A",
    "44C763",
    "44C234",
    "44C625",
    "44C626"
]

DX = 132847.0
DY = 1400405.9

results = []
for h in handles:
    try:
        ent = doc.HandleToObject(h)
        oname = ent.ObjectName
        layer = ent.Layer
        
        info = {
            "handle": h,
            "type": oname,
            "layer": layer
        }
        
        try:
            min_pt, max_pt = ent.GetBoundingBox()
            info["bbox_cad"] = {"min": [min_pt[0], min_pt[1]], "max": [max_pt[0], max_pt[1]]}
            info["bbox_rvt"] = {
                "min": [(min_pt[0] + DX) / 1000.0, (min_pt[1] + DY) / 1000.0],
                "max": [(max_pt[0] + DX) / 1000.0, (max_pt[1] + DY) / 1000.0]
            }
        except Exception as e:
            info["bbox_err"] = str(e)
            
        if oname == "AcDbLine":
            sp = list(ent.StartPoint)
            ep = list(ent.EndPoint)
            info["start_cad"] = sp
            info["end_cad"] = ep
            info["start_rvt"] = [(sp[0] + DX) / 1000.0, (sp[1] + DY) / 1000.0]
            info["end_rvt"] = [(ep[0] + DX) / 1000.0, (ep[1] + DY) / 1000.0]
            
        elif oname == "AcDbPolyline":
            coords = list(ent.Coordinates)
            pts_cad = []
            pts_rvt = []
            for j in range(0, len(coords), 2):
                x = coords[j]
                y = coords[j+1]
                pts_cad.append([x, y])
                pts_rvt.append([(x + DX) / 1000.0, (y + DY) / 1000.0])
            info["points_cad"] = pts_cad
            info["points_rvt"] = pts_rvt
            info["closed"] = ent.Closed
            
        results.append(info)
    except Exception as ex:
        results.append({"handle": h, "error": str(ex)})

out_file = r"D:\Dropbox\_Documents\RevitAI\scratch\handles_21_dump.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"Dumped {len(results)} entities to {out_file}")
