import json

with open(r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\selected_3walls_1door.json", "r", encoding="utf-8") as f:
    items = json.load(f)

print(f"Total items: {len(items)}")

# Print texts
texts = [it for it in items if "text" in it]
for t in texts:
    print(f"TEXT: '{t['text']}' at {t.get('insertion')}")

# Print S5 elements
s5 = [it for it in items if it['layer'] == 'S5']
print(f"\n--- S5 Elements ({len(s5)}) ---")
for s in s5:
    bb = s['bb_min'], s['bb_max']
    print(f"{s['objectName']} (handle {s['handle']}): bb={bb}")
    if 'start' in s:
        print(f"   Line: {s['start']} -> {s['end']}, len={s.get('length'):.1f}")
    if 'coords' in s:
        print(f"   Poly: {s['coords']}, len={s.get('length'):.1f}")

# Overall bounding box of selection
xs = [it['bb_min'][0] for it in items] + [it['bb_max'][0] for it in items]
ys = [it['bb_min'][1] for it in items] + [it['bb_max'][1] for it in items]
min_x, max_x = min(xs), max(xs)
min_y, max_y = min(ys), max(ys)
print(f"\nOverall CAD BoundingBox: X=[{min_x:.1f}, {max_x:.1f}], Y=[{min_y:.1f}, {max_y:.1f}]")
print(f"Width = {max_x - min_x:.1f}, Height = {max_y - min_y:.1f}")

# Check with Tang 2 transform (DX = +70950.0, DY = +1400406.0)
rvt_x1 = (min_x + 70950.0) / 1000.0
rvt_x2 = (max_x + 70950.0) / 1000.0
rvt_y1 = (min_y + 1400406.0) / 1000.0
rvt_y2 = (max_y + 1400406.0) / 1000.0
print(f"If Tang 2: X_rvt=[{rvt_x1:.3f}m, {rvt_x2:.3f}m], Y_rvt=[{rvt_y1:.3f}m, {rvt_y2:.3f}m]")

# Check with Tang 1 transform (DX = +132847.0, DY = +1400405.9)
rvt1_x1 = (min_x + 132847.0) / 1000.0
rvt1_x2 = (max_x + 132847.0) / 1000.0
rvt1_y1 = (min_y + 1400405.9) / 1000.0
rvt1_y2 = (max_y + 1400405.9) / 1000.0
print(f"If Tang 1: X_rvt=[{rvt1_x1:.3f}m, {rvt1_x2:.3f}m], Y_rvt=[{rvt1_y1:.3f}m, {rvt1_y2:.3f}m]")
