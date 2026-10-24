import json

with open(r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\selected_3walls_1door.json", "r", encoding="utf-8") as f:
    items = json.load(f)

for idx, it in enumerate(items):
    bb_min = it['bb_min']
    bb_max = it['bb_max']
    print(f"[{idx}] {it['layer']} {it['objectName']} (handle {it['handle']}): bb_min=({bb_min[0]:.2f}, {bb_min[1]:.2f}), bb_max=({bb_max[0]:.2f}, {bb_max[1]:.2f})")
    if 'coords' in it:
        print(f"    raw coords: {it['coords'][:2]}")
    if 'start' in it:
        print(f"    raw line: {it['start']} -> {it['end']}")
