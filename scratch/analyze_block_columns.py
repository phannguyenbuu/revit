import json

with open(r"scratch\block_columns_entities.json", encoding="utf-8") as f:
    data = json.load(f)

ins_cad = data["insertion_point_cad"]
scale = data["scale"]
rot = data["rotation"]

print(f"Total entities: {len(data['entities'])}")

# Check what block references are nested inside
nested_blocks = [e for e in data["entities"] if e["type"] == "AcDbBlockReference"]
print(f"Nested block references count: {len(nested_blocks)}")

polylines = [e for e in data["entities"] if "Polyline" in e["type"]]
print(f"Polylines count: {len(polylines)}")

hatches = [e for e in data["entities"] if e["type"] == "AcDbHatch"]
print(f"Hatches count: {len(hatches)}")

# Let's inspect polylines bounding boxes transformed to RVT coordinates
# Note: For entities inside a block definition, their coordinates are in the block definition's local coordinate system.
# When the block is inserted at ins_cad, an entity coordinate (x_local, y_local) translates to:
# X_cad = ins_cad[0] + x_local
# Y_cad = ins_cad[1] + y_local
# (Since scale is (1,1,1) and rotation is 0)
# Then RVT coordinate is:
# X_rvt = (X_cad + 132847.0) / 1000.0
# Y_rvt = (Y_cad + 1400405.9) / 1000.0

poly_boxes = []
for p in polylines:
    if "box_local" in p:
        b = p["box_local"]
        x1_cad = ins_cad[0] + b[0]
        y1_cad = ins_cad[1] + b[1]
        x2_cad = ins_cad[0] + b[2]
        y2_cad = ins_cad[1] + b[3]
        
        x1_rvt = round((x1_cad + 132847.0) / 1000.0, 4)
        y1_rvt = round((y1_cad + 1400405.9) / 1000.0, 4)
        x2_rvt = round((x2_cad + 132847.0) / 1000.0, 4)
        y2_rvt = round((y2_cad + 1400405.9) / 1000.0, 4)
        
        w = round(abs(x2_rvt - x1_rvt), 4)
        h = round(abs(y2_rvt - y1_rvt), 4)
        poly_boxes.append({
            "idx": p["idx"],
            "layer": p["layer"],
            "box_rvt": [x1_rvt, y1_rvt, x2_rvt, y2_rvt],
            "w": w,
            "h": h,
            "pts_count": p.get("pts_count", 0),
            "closed": p.get("closed", False)
        })

print("\n--- SAMPLE POLYLINES (first 20) ---")
for pb in poly_boxes[:20]:
    print(f"[{pb['idx']}] Lay:{pb['layer']} Closed:{pb['closed']} Pts:{pb['pts_count']} W={pb['w']*1000:.0f} H={pb['h']*1000:.0f} Box:{pb['box_rvt']}")

# Let's inspect the nested block references as well
print("\n--- NESTED BLOCK REFERENCES ---")
for nb in nested_blocks[:10]:
    print(f"[{nb['idx']}] Lay:{nb['layer']} Handle:{nb['handle']}")
