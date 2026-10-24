import json

with open(r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\cad_tang3_extracted.json", "r", encoding="utf-8") as f:
    data = json.load(f)

cols = [it for it in data["items"] if it.get("blockName") in ["cot1-2", "cot"]]
print(f"Found {len(cols)} column blocks")

# In Revit:
# Column A1: (1.750, 0.000) or near Grid 1 (1.650) & Grid A (0.000)
# Column A11: near Grid 11 (36.050) & Grid A (0.000)
# Column E2: near Grid 2 (5.250) & Grid E (13.200)

cad_col_xs = sorted(list(set([round(c["insertion"][0], 1) for c in cols])))
cad_col_ys = sorted(list(set([round(c["insertion"][1], 1) for c in cols])))

print(f"Unique Column CAD X coordinates ({len(cad_col_xs)}):")
for x in cad_col_xs:
    print(f"  {x}")

print(f"\nUnique Column CAD Y coordinates ({len(cad_col_ys)}):")
for y in cad_col_ys:
    print(f"  {y}")

# Compare with Revit grid coordinates:
# Revit Grids:
# 1: 1.65m, 2: 5.25m, 3: 8.85m, 4: 12.45m, 5: 16.05m, 6: 18.85m, 7: 21.65m, 8: 25.25m, 9: 28.85m, 10: 32.45m, 11: 36.05m
# Grids spacing in X:
# 2-1: 3.6m
# 3-2: 3.6m
# 4-3: 3.6m
# 5-4: 3.6m
# 6-5: 2.8m
# 7-6: 2.8m
# 8-7: 3.6m
# 9-8: 3.6m
# 10-9: 3.6m
# 11-10: 3.6m

# Notice CAD column X diffs:
print("\nCAD column X consecutive diffs:")
for i in range(1, len(cad_col_xs)):
    diff = cad_col_xs[i] - cad_col_xs[i-1]
    print(f"  {cad_col_xs[i]} - {cad_col_xs[i-1]} = {diff:.1f}")

# First column X in CAD vs Revit Column 1 X:
# In Level 2: DX was +70950.0
# Let's find DX:
revit_col1_x = 1750.0 # mm
cad_col1_x = cad_col_xs[0]
dx_calc = revit_col1_x - cad_col1_x
print(f"\nCalculated DX: {dx_calc:.1f} mm")

# In Level 2: DY was +1400406.0
# Revit Column A Y is 0.0 (or -100 to +100 mm)
cad_colA_y = cad_col_ys[0]
dy_calc = 0.0 - cad_colA_y
print(f"Calculated DY: {dy_calc:.1f} mm")
