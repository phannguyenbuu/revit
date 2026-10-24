import json

with open(r'C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\cad_selection_tang2.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

# Inspect 32-CUA blocks
c1000 = [it for it in items if it['layer'] == '32-CUA']
print(f"Total in 32-CUA: {len(c1000)}")
for it in c1000:
    print(f"  {it['type']} {it.get('name')} at {it.get('point')}")

# Also check polylines and lines on A-Door
adoor = [it for it in items if it['layer'] == 'A-Door']
print(f"\nTotal in A-Door: {len(adoor)}")
for it in adoor:
    if it['type'] == 'AcDbPolyline':
        pts = it.get('points', [])
        # check width/bounding box
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        print(f"  Pline {len(pts)} pts: X [{min(xs):.2f}, {max(xs):.2f}], Y [{min(ys):.2f}, {max(ys):.2f}]")
