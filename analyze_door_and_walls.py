import json

with open(r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\selected_3walls_1door.json", "r", encoding="utf-8") as f:
    items = json.load(f)

def to_rvt(x, y):
    return (x + 70950.0) / 1000.0, (y + 1400406.0) / 1000.0

door_items = [it for it in items if it['layer'] == 'A-Door']
print(f"Door elements count: {len(door_items)}")
for it in door_items:
    t = it['objectName']
    h = it['handle']
    bb_min = to_rvt(it['bb_min'][0], it['bb_min'][1])
    bb_max = to_rvt(it['bb_max'][0], it['bb_max'][1])
    print(f"Door {t} {h}: bb=[({bb_min[0]:.4f}, {bb_min[1]:.4f}), ({bb_max[0]:.4f}, {bb_max[1]:.4f})]")
    if t == 'AcDbLine':
        p1 = to_rvt(it['start'][0], it['start'][1])
        p2 = to_rvt(it['end'][0], it['end'][1])
        print(f"   Line: ({p1[0]:.4f}, {p1[1]:.4f}) -> ({p2[0]:.4f}, {p2[1]:.4f}), len={it['length']:.1f}")
    elif 'Polyline' in t:
        pts = [to_rvt(c[0], c[1]) for c in it['coords']]
        pts_str = " -> ".join([f"({p[0]:.4f}, {p[1]:.4f})" for p in pts])
        print(f"   Poly: {pts_str}")
