import json

with open(r"scratch\cad_selection_5walls_d5.json", encoding="utf-8") as f:
    items = json.load(f)

print("Listing all non-door items:")
for it in items:
    if it['layer'] not in ['A-Door', 'TBI']:
        print(f"[{it['idx']}] Handle: {it['handle']} | Type: {it['type']} | Lay: {it['layer']} | Box: {it['box_rvt']}")
        if "pts_rvt" in it:
            print(f"      Pts: {it['pts_rvt']}")
        if "start_rvt" in it:
            print(f"      Line: {it['start_rvt']} -> {it['end_rvt']}")
