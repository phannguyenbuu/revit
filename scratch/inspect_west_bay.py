import json

with open(r'C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\cad_selection_tang2.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

# Inspect West bay (X: 0 to 4.5, Y: 5.0 to 13.5)
west_items = []
for it in items:
    in_zone = False
    if it['type'] == 'AcDbLine':
        sp, ep = it['start'], it['end']
        if (0.0 <= sp[0] <= 4.5 and 5.0 <= sp[1] <= 13.5) or (0.0 <= ep[0] <= 4.5 and 5.0 <= ep[1] <= 13.5):
            in_zone = True
    elif it['type'] == 'AcDbPolyline':
        pts = it.get('points', [])
        if any(0.0 <= p[0] <= 4.5 and 5.0 <= p[1] <= 13.5 for p in pts):
            in_zone = True
    elif it['type'] in ('AcDbText', 'AcDbMText', 'AcDbBlockReference'):
        p = it.get('point', [0, 0])
        if 0.0 <= p[0] <= 4.5 and 5.0 <= p[1] <= 13.5:
            in_zone = True
    if in_zone:
        west_items.append(it)

print(f"Total entities in West bay: {len(west_items)}")
for it in west_items:
    if it['type'] == 'AcDbLine':
        print(f"  Line lay={it['layer']} ({it['start'][0]:.2f}, {it['start'][1]:.2f}) -> ({it['end'][0]:.2f}, {it['end'][1]:.2f})")
    elif it['type'] == 'AcDbPolyline':
        pts = it.get('points', [])
        print(f"  Pline lay={it['layer']} {len(pts)} pts: {pts[0]} -> {pts[-1]}")
    elif it['type'] in ('AcDbText', 'AcDbMText'):
        print(f"  Text: {it.get('text')} at {it.get('point')}")
    elif it['type'] == 'AcDbBlockReference':
        print(f"  Block: {it.get('name')} at {it.get('point')}")
