import json

with open(r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\cad_tang3_extracted.json", "r", encoding="utf-8") as f:
    data = json.load(f)

items = data["items"]
print(f"Total items: {len(items)}")

# 1. Find text annotations of grids (1, 2, 3... 11 and A, B, C, D, E)
grid_texts = []
for it in items:
    if 'text' in it:
        txt = it['text'].strip()
        if txt in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', 'A', 'B', 'C', 'D', 'E']:
            grid_texts.append({"text": txt, "pos": it['insertion'], "handle": it['handle']})

print(f"Found {len(grid_texts)} grid texts:")
for gt in grid_texts:
    print(f"  Grid {gt['text']}: CAD=({gt['pos'][0]:.1f}, {gt['pos'][1]:.1f})")

# In Revit:
# Grid 1: X = 1.650m
# Grid 2: X = 5.250m
# Grid 3: X = 8.850m
# Grid 4: X = 12.450m
# Grid 5: X = 16.050m
# Grid 6: X = 18.850m
# Grid 7: X = 21.650m
# Grid 8: X = 25.250m
# Grid 9: X = 28.850m
# Grid 10: X = 32.450m (or 32.550m)
# Grid 11: X = 36.050m
# Grid A: Y = 0.000m
# Grid B: Y = 5.400m
# Grid C: Y = 7.800m
# Grid D: Y = 11.400m
# Grid E: Y = 13.200m

# Let's check candidate DX and DY
revit_grids_x = {
    '1': 1650.0, '2': 5250.0, '3': 8850.0, '4': 12450.0, '5': 16050.0,
    '6': 18850.0, '7': 21650.0, '8': 25250.0, '9': 28850.0, '10': 32450.0, '11': 36050.0
}
revit_grids_y = {
    'A': 0.0, 'B': 5400.0, 'C': 7800.0, 'D': 11400.0, 'E': 13200.0
}

dx_estimates = []
for gt in grid_texts:
    t = gt['text']
    if t in revit_grids_x:
        # gt['pos'][0] is near the grid line X
        # In CAD, Grid text is at the end of the line, X is aligned with the grid line!
        cad_x = gt['pos'][0]
        # In previous Tang 2: CAD_X was around -70950 + 1650 = -69300
        # Here CAD_X for Grid 1:
        # dx = revit_x - cad_x
        dx_est = revit_grids_x[t] - cad_x
        dx_estimates.append((t, dx_est))

print("\nDX estimates from Grid texts:")
for t, dx in dx_estimates:
    print(f"  Grid {t}: DX = {dx:.1f}")

dy_estimates = []
for gt in grid_texts:
    t = gt['text']
    if t in revit_grids_y:
        cad_y = gt['pos'][1]
        dy_est = revit_grids_y[t] - cad_y
        dy_estimates.append((t, dy_est))

print("\nDY estimates from Grid texts:")
for t, dy in dy_estimates:
    print(f"  Grid {t}: DY = {dy:.1f}")
