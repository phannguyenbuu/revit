import json

with open(r'C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\cad_selection_tang2.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

layer_geom = {}
for it in items:
    t = it['type']
    lay = it['layer']
    if t in ('AcDbLine', 'AcDbPolyline'):
        layer_geom[lay] = layer_geom.get(lay, 0) + 1

print("Lines / Polylines count by layer:")
for lay, c in sorted(layer_geom.items(), key=lambda x: -x[1]):
    print(f"  {lay}: {c}")
