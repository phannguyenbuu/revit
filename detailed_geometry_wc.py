import json

with open(r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\selected_3walls_1door.json", "r", encoding="utf-8") as f:
    items = json.load(f)

def to_rvt(x, y):
    return (x + 70950.0) / 1000.0, (y + 1400406.0) / 1000.0

print("=== S5 LAYER (WALLS) ===")
for it in items:
    if it['layer'] == 'S5':
        h = it['handle']
        t = it['objectName']
        if t == 'AcDbLine':
            p1 = to_rvt(it['start'][0], it['start'][1])
            p2 = to_rvt(it['end'][0], it['end'][1])
            length = it['length']
            print(f"Line {h}: ({p1[0]:.4f}, {p1[1]:.4f}) -> ({p2[0]:.4f}, {p2[1]:.4f}), len={length:.1f}mm")
        elif 'Polyline' in t:
            coords = it['coords']
            pts = [to_rvt(c[0], c[1]) for c in coords]
            pts_str = " -> ".join([f"({p[0]:.4f}, {p[1]:.4f})" for p in pts])
            print(f"Poly {h}: {pts_str}, len={it['length']:.1f}mm, closed={it['closed']}")

print("\n=== A-DOOR LAYER (DOOR) ===")
door_items = [it for it in items if it['layer'] == 'A-Door']
xs = [it['bb_min'][0] for it in door_items] + [it['bb_max'][0] for it in door_items]
ys = [it['bb_min'][1] for it in door_items] + [it['bb_max'][1] for it in door_items]
d_min = to_rvt(min(xs), min(ys))
d_max = to_rvt(max(xs), max(ys))
print(f"Door bounding box in Revit: ({d_min[0]:.4f}, {d_min[1]:.4f}) to ({d_max[0]:.4f}, {d_max[1]:.4f})")
print(f"Door width X = {(d_max[0]-d_min[0])*1000:.1f}mm, height Y = {(d_max[1]-d_min[1])*1000:.1f}mm")

# Check circle / tag
for it in items:
    if it['layer'] in ['TBI', 'NET THAY']:
        print(f"Tag/Symbol {it['layer']} {it['objectName']}: bb={it['bb_min']}, {it['bb_max']}")
