import json

with open(r'C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\cad_selection_tang2.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

# Group by layer
layers = {}
for it in items:
    lay = it['layer']
    if lay not in layers:
        layers[lay] = []
    layers[lay].append(it)

print("Entities by layer in user's selection:")
for lay, ents in sorted(layers.items(), key=lambda x: -len(x[1])):
    types = {}
    for e in ents:
        types[e['type']] = types.get(e['type'], 0) + 1
    print(f"Layer '{lay}': {len(ents)} items -> {types}")
    # print sample
    for e in ents[:3]:
        if e['type'] == 'AcDbLine':
            print(f"    Line ({e['start'][0]:.2f}, {e['start'][1]:.2f}) -> ({e['end'][0]:.2f}, {e['end'][1]:.2f})")
        elif e['type'] == 'AcDbPolyline':
            pts = e.get('points', [])
            print(f"    Pline {len(pts)} pts: {pts[:2]}")
        elif e['type'] in ('AcDbText', 'AcDbMText'):
            print(f"    Text: {e.get('text')} at {e.get('point')}")
        elif e['type'] == 'AcDbBlockReference':
            print(f"    Block: {e.get('name')} at {e.get('point')}")
