import json

DX = 132847.0
DY = 1400405.9

with open(r"D:\Dropbox\_Documents\RevitAI\scratch\k1_crossing_dump.txt", "r", encoding="utf-8") as f:
    lines = [l.strip() for l in f if l.strip()]

for l in lines[1:]:
    parts = l.split("|")
    if len(parts) >= 5:
        h, obj_type, layer, pmin_str, pmax_str = parts[:5]
        pmin = [float(x) for x in pmin_str.split(",")]
        pmax = [float(x) for x in pmax_str.split(",")]
        pmin_rvt = [(pmin[0] + DX) / 1000.0, (pmin[1] + DY) / 1000.0]
        pmax_rvt = [(pmax[0] + DX) / 1000.0, (pmax[1] + DY) / 1000.0]
        
        # Check if inside or near 44C786 (X in [34.3, 34.9], Y in [-0.4, 0.2])
        if (34.3 <= pmin_rvt[0] <= 34.9 or 34.3 <= pmax_rvt[0] <= 34.9) and (-0.4 <= pmin_rvt[1] <= 0.2):
            print(f"Near 44C786: handle={h}, type={obj_type}, layer={layer}, X=[{pmin_rvt[0]:.3f}, {pmax_rvt[0]:.3f}], Y=[{pmin_rvt[1]:.3f}, {pmax_rvt[1]:.3f}]")

        # Check if inside or near 44C779 (X in [35.5, 36.1], Y in [-0.4, 0.2])
        if (35.5 <= pmin_rvt[0] <= 36.1 or 35.5 <= pmax_rvt[0] <= 36.1) and (-0.4 <= pmin_rvt[1] <= 0.2):
            print(f"Near 44C779: handle={h}, type={obj_type}, layer={layer}, X=[{pmin_rvt[0]:.3f}, {pmax_rvt[0]:.3f}], Y=[{pmin_rvt[1]:.3f}, {pmax_rvt[1]:.3f}]")
