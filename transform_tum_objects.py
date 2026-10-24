import json

with open(r'C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\cad_selection_tang_tum.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

DX = -113999.1
DY = 1400405.9

def to_rvt(x, y):
    return round((x + DX) / 1000.0, 3), round((y + DY) / 1000.0, 3)

print("=== TRANSFORMED OBJECTS IN REVIT COORDINATES ===")

# Columns (COT)
for it in d['items']:
    if it['layer'] == 'COT':
        bb = it['bbox']
        p1 = to_rvt(bb['min'][0], bb['min'][1])
        p2 = to_rvt(bb['max'][0], bb['max'][1])
        print(f"COL: bbox=[{p1} - {p2}], center=({(p1[0]+p2[0])/2:.3f}, {(p1[1]+p2[1])/2:.3f})")

# Walls (S5)
print("\n--- S5 (Walls) ---")
for it in d['items']:
    if it['layer'] == 'S5':
        if it['objectName'] == 'AcDbLine':
            p1 = to_rvt(it['start'][0], it['start'][1])
            p2 = to_rvt(it['end'][0], it['end'][1])
            print(f"Line (H={it['handle']}): {p1} -> {p2}")
        elif it['objectName'] == 'AcDbPolyline':
            coords = it['coords']
            pts = []
            for i in range(0, len(coords), 2):
                pts.append(to_rvt(coords[i], coords[i+1]))
            print(f"Poly (H={it['handle']}): {pts}")

# Door (A-Door, TBI)
print("\n--- Door D4 ---")
for it in d['items']:
    if it['layer'] == 'TBI':
        ins = to_rvt(it['insertion'][0], it['insertion'][1])
        print(f"Text '{it['text']}': {ins}")
    elif it['layer'] == 'A-Door' and it['objectName'] == 'AcDbLine':
        p1 = to_rvt(it['start'][0], it['start'][1])
        p2 = to_rvt(it['end'][0], it['end'][1])
        print(f"Door Line: {p1} -> {p2}")
    elif it['layer'] == 'A-Door' and it['objectName'] == 'AcDbArc':
        c = to_rvt(it['center'][0], it['center'][1])
        r = round(it['radius'] / 1000.0, 3)
        print(f"Door Arc: center={c}, radius={r}")
