import json

with open(r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\cad_tang3_extracted.json", "r", encoding="utf-8") as f:
    data = json.load(f)

items = data["items"]

s5 = [it for it in items if it['layer'] == 'S5']
print(f"Total S5 items: {len(s5)}")

xs = []
ys = []
for it in s5:
    if 'bb' in it:
        xs.extend([it['bb'][0], it['bb'][2]])
        ys.extend([it['bb'][1], it['bb'][3]])

min_x, max_x = min(xs), max(xs)
min_y, max_y = min(ys), max(ys)

print(f"S5 Bounding Box in CAD:")
print(f"  X: [{min_x:.3f}, {max_x:.3f}], width = {max_x - min_x:.3f}")
print(f"  Y: [{min_y:.3f}, {max_y:.3f}], height = {max_y - min_y:.3f}")

# In Revit:
# Building exterior wall footprint:
# West wall (Trục 1): X_min = 0.550m
# East wall (Trục 11): X_max = 37.150m
# South wall (Trục A): Y_min = -0.100m or 0.000m (or center 0.0m)
# North wall: Y_max = 13.200m or 14.900m (stair towers)
# Width = 37.150 - 0.550 = 36.600m = 36600mm!

# Compare with S5 width in CAD:
print(f"Expected Revit width: 36600.0 mm. S5 width in CAD: {max_x - min_x:.3f} mm")

# Calculate DX:
# If min_x corresponds to X_rvt = 0.550m = 550.0mm:
dx_from_min = 550.0 - min_x
dx_from_max = 37150.0 - max_x
print(f"DX from min X: {dx_from_min:.3f} mm")
print(f"DX from max X: {dx_from_max:.3f} mm")

# Calculate DY:
# If min_y corresponds to Y_rvt = 0.0m = 0.0mm (or -100.0mm):
dy_from_min = 0.0 - min_y # or -100 - min_y
print(f"DY from min Y (0.0): {dy_from_min:.3f} mm")
print(f"DY from min Y (-100.0): {-100.0 - min_y:.3f} mm")
