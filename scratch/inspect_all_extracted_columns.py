import json

with open(r"scratch\extracted_columns.json", encoding="utf-8") as f:
    cols = json.load(f)

print(f"Total columns: {len(cols)}")

size_counts = {}
for c in cols:
    w = c["max_item_size_mm"][0]
    h = c["max_item_size_mm"][1]
    # Check if envelope or max_item should be used
    ew = c["envelope_size_mm"][0]
    eh = c["envelope_size_mm"][1]
    
    # Since small sub-millimeter offsets might make 401 instead of 400, round to nearest 10mm
    rw = round(w / 10.0) * 10
    rh = round(h / 10.0) * 10
    
    erw = round(ew / 10.0) * 10
    erh = round(eh / 10.0) * 10
    
    s = f"{rw}x{rh}"
    size_counts[s] = size_counts.get(s, 0) + 1
    
    # Also compare with max item
    # print all columns
    print(f"Col #{c['cluster_id']:02d}: Center=({c['center'][0]:.3f}, {c['center'][1]:.3f}) | Size={rw}x{rh} (Env={erw}x{erh}) | Box=[{c['max_item_box'][0]:.3f}, {c['max_item_box'][1]:.3f}, {c['max_item_box'][2]:.3f}, {c['max_item_box'][3]:.3f}]")

print("\nSummary of Column Sizes:")
for s, cnt in sorted(size_counts.items(), key=lambda x: -x[1]):
    print(f"  {s}: {cnt} columns")
