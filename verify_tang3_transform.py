import json

with open(r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\cad_tang3_extracted.json", "r", encoding="utf-8") as f:
    data = json.load(f)

items = data["items"]

# Filter S5 lines (walls)
s5_lines = [it for it in items if it['layer'] == 'S5' and it['objectName'] == 'AcDbLine']
print(f"Total S5 lines: {len(s5_lines)}")

# Let's find long horizontal lines (Perimeter walls Wall A, Wall B, Wall C)
# In Revit:
# Wall A is at Y = 0.0m (X from 0.55m to 37.15m)
# Wall B is at Y = 5.4m
# Wall C is at Y = 7.8m
# Wall D is at Y = 11.4m or 13.2m

DY = 1400405.9

# Check horizontal lines with length > 20000mm
long_h_lines = []
for l in s5_lines:
    if abs(l['start'][1] - l['end'][1]) < 1.0 and l['length'] > 20000:
        cad_y = l['start'][1]
        rvt_y = (cad_y + DY) / 1000.0
        min_x = min(l['start'][0], l['end'][0])
        max_x = max(l['start'][0], l['end'][0])
        long_h_lines.append({"cad_y": cad_y, "rvt_y": round(rvt_y, 4), "len": l['length'], "cad_x_range": [min_x, max_x]})

print("Long horizontal S5 lines:")
for lh in long_h_lines:
    print(lh)

# Also check vertical lines (Wall 1 at west, Wall 11 at east)
long_v_lines = []
for l in s5_lines:
    if abs(l['start'][0] - l['end'][0]) < 1.0 and l['length'] > 10000:
        cad_x = l['start'][0]
        min_y = min(l['start'][1], l['end'][1])
        max_y = max(l['start'][1], l['end'][1])
        long_v_lines.append({"cad_x": cad_x, "len": l['length'], "cad_y_range": [min_y, max_y]})

print("\nLong vertical S5 lines:")
for lv in long_v_lines:
    print(lv)
