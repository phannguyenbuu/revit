import json

DX = 132847.0
DY = 1400405.9

with open(r"D:\Dropbox\_Documents\RevitAI\scratch\k1_crossing_dump.txt", "r", encoding="utf-8") as f:
    lines = [l.strip() for l in f if l.strip()]

s5_items = []
for l in lines[1:]:
    parts = l.split("|")
    if len(parts) >= 5:
        h, obj_type, layer, pmin_str, pmax_str = parts[:5]
        pmin = [float(x) for x in pmin_str.split(",")]
        pmax = [float(x) for x in pmax_str.split(",")]
        pmin_rvt = [(pmin[0] + DX) / 1000.0, (pmin[1] + DY) / 1000.0]
        pmax_rvt = [(pmax[0] + DX) / 1000.0, (pmax[1] + DY) / 1000.0]
        if layer == "S5":
            s5_items.append({
                "handle": h,
                "type": obj_type,
                "layer": layer,
                "bbox_rvt": [pmin_rvt, pmax_rvt]
            })

print(f"Total S5 items: {len(s5_items)}")
for it in s5_items:
    print(f"Handle: {it['handle']}, Type: {it['type']}, X: [{it['bbox_rvt'][0][0]:.3f}, {it['bbox_rvt'][1][0]:.3f}], Y: [{it['bbox_rvt'][0][1]:.3f}, {it['bbox_rvt'][1][1]:.3f}]")
