import sys, os, json, ctypes
sys.stdout.reconfigure(encoding='utf-8')

# Ensure desktop access for COM on Windows
u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
try:
    doc = acad.ActiveDocument
except Exception:
    doc = acad.Documents.Item(0)

print(f"AutoCAD Document: {doc.Name}")

pf = doc.PickfirstSelectionSet
act = doc.ActiveSelectionSet
ss = pf if pf.Count > 0 else act
print(f"Selected entities count: {ss.Count}")

DX = 132847.0
DY = 1400405.9

items = []
for i in range(ss.Count):
    ent = ss.Item(i)
    obj_name = ent.ObjectName
    if obj_name != "AcDbPolyline":
        print(f"Skipping non-polyline object: {obj_name}")
        continue
    
    min_pt, max_pt = ent.GetBoundingBox()
    min_x_rvt_mm = min_pt[0] + DX
    max_x_rvt_mm = max_pt[0] + DX
    min_y_rvt_mm = min_pt[1] + DY
    max_y_rvt_mm = max_pt[1] + DY
    
    coords = list(ent.Coordinates)
    pts_cad = []
    pts_rvt_mm = []
    for j in range(0, len(coords), 2):
        cx = coords[j]
        cy = coords[j+1]
        pts_cad.append([cx, cy])
        pts_rvt_mm.append([cx + DX, cy + DY])
    
    # Determine architectural name and role
    mid_x_mm = (min_x_rvt_mm + max_x_rvt_mm) / 2.0
    mid_y_mm = (min_y_rvt_mm + max_y_rvt_mm) / 2.0
    
    if mid_x_mm < 10000.0:
        name = "MẶT BẰNG CHI TIẾT SẢNH CHÍNH & TAM CẤP"
        short_name = "CT SẢNH CHÍNH"
    elif mid_y_mm > 6000.0:
        name = "MẶT BẰNG CHI TIẾT CẦU THANG 2 & KHU VỆ SINH"
        short_name = "CT THANG 2 & WC"
    else:
        name = "MẶT BẰNG CHI TIẾT TAM CẤP 5 BẬC SẢNH PHỤ"
        short_name = "CT TAM CẤP 5 BẬC"
        
    items.append({
        "index": i,
        "handle": ent.Handle,
        "layer": ent.Layer,
        "name": name,
        "short_name": short_name,
        "points_cad": pts_cad,
        "points_rvt_mm": pts_rvt_mm,
        "bbox_cad": {
            "min": [min_pt[0], min_pt[1]],
            "max": [max_pt[0], max_pt[1]]
        },
        "bbox_rvt_mm": {
            "min": [min_x_rvt_mm, min_y_rvt_mm],
            "max": [max_x_rvt_mm, max_y_rvt_mm]
        }
    })

# Sort items by X ascending
items.sort(key=lambda x: x["bbox_rvt_mm"]["min"][0])

out_path = r"D:\Dropbox\_Documents\RevitAI\scratch\cad_callout_polylines.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(items, f, indent=2, ensure_ascii=False)

print(f"Exported {len(items)} callout polylines to {out_path}:")
for it in items:
    b = it['bbox_rvt_mm']
    print(f"  - [{it['handle']}] {it['name']}: X=[{b['min'][0]:.0f}, {b['max'][0]:.0f}], Y=[{b['min'][1]:.0f}, {b['max'][1]:.0f}] (WxH = {b['max'][0]-b['min'][0]:.0f} x {b['max'][1]-b['min'][1]:.0f} mm)")
