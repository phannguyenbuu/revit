import json

with open(r'C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\cad_selection_tang2.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

# Inspect entities in WC area (X: 33 to 37.5, Y: 7.8 to 13.5)
wc_items = []
for it in items:
    # check if point or line in WC area
    in_wc = False
    if it['type'] == 'AcDbLine':
        sp, ep = it['start'], it['end']
        if (33.0 <= sp[0] <= 37.5 and 7.5 <= sp[1] <= 13.5) or (33.0 <= ep[0] <= 37.5 and 7.5 <= ep[1] <= 13.5):
            in_wc = True
    elif it['type'] == 'AcDbPolyline':
        pts = it.get('points', [])
        if any(33.0 <= p[0] <= 37.5 and 7.5 <= p[1] <= 13.5 for p in pts):
            in_wc = True
    elif it['type'] in ('AcDbText', 'AcDbMText', 'AcDbBlockReference'):
        p = it.get('point', [0, 0])
        if 33.0 <= p[0] <= 37.5 and 7.5 <= p[1] <= 13.5:
            in_wc = True
    if in_wc:
        wc_items.append(it)

print(f"Total entities in WC area: {len(wc_items)}")
for it in wc_items:
    if it['type'] == 'AcDbLine':
        print(f"  Line lay={it['layer']} ({it['start'][0]:.2f}, {it['start'][1]:.2f}) -> ({it['end'][0]:.2f}, {it['end'][1]:.2f})")
    elif it['type'] == 'AcDbPolyline':
        pts = it.get('points', [])
        print(f"  Pline lay={it['layer']} {len(pts)} pts: {pts[0]} -> {pts[-1]}")
    elif it['type'] in ('AcDbText', 'AcDbMText'):
        print(f"  Text: {it.get('text')} at {it.get('point')}")
