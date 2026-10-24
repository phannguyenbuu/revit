import json

with open(r"scratch\extracted_columns.json", encoding="utf-8") as f:
    cols = json.load(f)

clean_cols = []

for c in cols:
    cid = c["cluster_id"]
    # Outer envelope box
    b = c["max_item_box"]
    # Check dimensions
    w_mm = round((b[2] - b[0]) * 1000)
    h_mm = round((b[3] - b[1]) * 1000)
    
    # Standardize to nearest 50mm
    w_std = int(round(w_mm / 50.0) * 50)
    h_std = int(round(h_mm / 50.0) * 50)
    
    # Center point in Revit coordinates
    cx = round((b[0] + b[2]) / 2.0, 4)
    cy = round((b[1] + b[3]) / 2.0, 4)
    
    # Grid snapping if very close (< 5mm)
    # X grids
    x_grids = [0.55, 4.35, 8.05, 11.65, 15.25, 18.85, 22.45, 26.05, 29.65, 33.35, 37.15]
    for xg in x_grids:
        if abs(cx - xg) < 0.01:
            cx = xg
            break
            
    # Y center lines:
    # Row 1 (Trục A zone): Y center is 0.100 (or 0.000 for 200x200)
    # Row 2 (Trục B zone): Y center is 5.300
    # Row 3 (Trục C zone): Y center is 7.900
    # Row 4 (Trục D zone): Y center is 13.100
    # Row 5 (Trục E zone): Y center is 14.900
    y_lines = [0.000, 0.100, 5.300, 7.900, 13.100, 14.900]
    for yl in y_lines:
        if abs(cy - yl) < 0.01:
            cy = yl
            break

    clean_cols.append({
        "id": cid,
        "x": cx,
        "y": cy,
        "width_mm": w_std,
        "depth_mm": h_std,
        "symbol_name": f"COT{w_std}X{h_std}",
        "raw_box": b
    })

# Sort clean columns by Y then X
clean_cols.sort(key=lambda c: (c["y"], c["x"]))

print(f"Total clean columns: {len(clean_cols)}")

rows = {}
for c in clean_cols:
    y_key = f"Y={c['y']:.3f}"
    rows.setdefault(y_key, []).append(c)

for y_key, clist in rows.items():
    print(f"\n--- {y_key} ({len(clist)} columns) ---")
    for c in clist:
        print(f"  Col @ ({c['x']:.3f}, {c['y']:.3f}) : {c['symbol_name']} (W={c['width_mm']} x D={c['depth_mm']})")

with open(r"scratch\columns_for_revit.json", "w", encoding="utf-8") as f:
    json.dump(clean_cols, f, indent=2)

print("\nSaved scratch\\columns_for_revit.json successfully.")
