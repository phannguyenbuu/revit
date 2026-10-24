import json

with open(r"scratch\cad_selection_3walls.json", encoding="utf-8") as f:
    items = json.load(f)

for it in items:
    print(f"{it['idx']}: {it['type']} | Lay: {it['layer']} | Handle: {it['handle']} | Box: {it['box_rvt']}")
