import json

with open(r'C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\cad_selection_tang2.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

net02_items = [it for it in items if it['layer'] == 'Net-02']
print(f"Total Net-02 items: {len(net02_items)}")

for it in net02_items:
    t = it['type']
    if t == 'AcDbLine':
        sp, ep = it['start'], it['end']
        dx, dy = ep[0]-sp[0], ep[1]-sp[1]
        length = (dx*dx + dy*dy)**0.5
        print(f"  Line ({sp[0]:.2f}, {sp[1]:.2f}) -> ({ep[0]:.2f}, {ep[1]:.2f}), len={length:.2f}m")
    elif t == 'AcDbPolyline':
        pts = it.get('points', [])
        print(f"  Pline with {len(pts)} pts: {pts[0]} ... {pts[-1]}")
