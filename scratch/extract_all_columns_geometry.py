import sys, ctypes, json
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument
blk_ref = doc.HandleToObject('497C83')

exploded = blk_ref.Explode()
print(f"Exploded into {len(exploded)} objects")

all_shapes = []

for idx, ent in enumerate(exploded):
    t = ent.ObjectName
    lay = ent.Layer
    p1, p2 = ent.GetBoundingBox()
    x1 = round((p1[0] + 132847.0) / 1000.0, 4)
    y1 = round((p1[1] + 1400405.9) / 1000.0, 4)
    x2 = round((p2[0] + 132847.0) / 1000.0, 4)
    y2 = round((p2[1] + 1400405.9) / 1000.0, 4)
    
    # If it's a block reference, what is its name?
    bname = ""
    if t == "AcDbBlockReference":
        bname = getattr(ent, 'EffectiveName', ent.Name)
        
    all_shapes.append({
        "idx": idx,
        "type": t,
        "layer": lay,
        "block": bname,
        "box": [min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)],
        "cx": round((x1 + x2) / 2.0, 4),
        "cy": round((y1 + y2) / 2.0, 4),
        "w": round(abs(x2 - x1), 4),
        "h": round(abs(y2 - y1), 4)
    })

# Delete exploded objects
for ent in exploded:
    try:
        ent.Delete()
    except:
        pass

print(f"Extracted {len(all_shapes)} shapes. Analyzing clusters...")

# Cluster shapes by center point within 0.35m
clusters = []
for s in all_shapes:
    matched = False
    for c in clusters:
        # Check distance between centers or bounding box overlap
        dx = abs(s["cx"] - c["cx"])
        dy = abs(s["cy"] - c["cy"])
        if dx < 0.35 and dy < 0.35:
            c["items"].append(s)
            matched = True
            break
    if not matched:
        clusters.append({
            "cx": s["cx"],
            "cy": s["cy"],
            "items": [s]
        })

print(f"Total column clusters identified: {len(clusters)}")

column_results = []
for i, c in enumerate(clusters):
    items = c["items"]
    # Outer envelope of all items in cluster
    min_x = min(it["box"][0] for it in items)
    min_y = min(it["box"][1] for it in items)
    max_x = max(it["box"][2] for it in items)
    max_y = max(it["box"][3] for it in items)
    
    # Also find the single item with maximum area
    max_item = max(items, key=lambda it: it["w"] * it["h"])
    
    env_w = round(max_x - min_x, 4)
    env_h = round(max_y - min_y, 4)
    
    center_x = round((min_x + max_x) / 2.0, 4)
    center_y = round((min_y + max_y) / 2.0, 4)
    
    col_info = {
        "cluster_id": i,
        "count": len(items),
        "center": [center_x, center_y],
        "envelope_box": [min_x, min_y, max_x, max_y],
        "envelope_size_mm": [round(env_w * 1000), round(env_h * 1000)],
        "max_item_box": max_item["box"],
        "max_item_size_mm": [round(max_item["w"] * 1000), round(max_item["h"] * 1000)],
        "max_item_block": max_item["block"],
        "items_summary": [f"{it['type']}({it.get('block','')})[{round(it['w']*1000)}x{round(it['h']*1000)}]" for it in items]
    }
    column_results.append(col_info)

# Sort columns by Y (bottom to top), then X (left to right)
column_results.sort(key=lambda col: (round(col["center"][1], 1), round(col["center"][0], 1)))

for col in column_results:
    env_str = f"{col['envelope_size_mm'][0]}x{col['envelope_size_mm'][1]}"
    max_str = f"{col['max_item_size_mm'][0]}x{col['max_item_size_mm'][1]}"
    print(f"Col @ ({col['center'][0]:.3f}, {col['center'][1]:.3f}) | Items: {col['count']} | Env: {env_str} | MaxItem: {max_str} ({col['max_item_block']})")
    if env_str != max_str:
        print(f"   --> DIFF! Env={env_str} vs MaxItem={max_str}. Items: {col['items_summary']}")

with open(r"scratch\extracted_columns.json", "w", encoding="utf-8") as f:
    json.dump(column_results, f, indent=2)

print(f"\nSaved {len(column_results)} columns to scratch\\extracted_columns.json")
