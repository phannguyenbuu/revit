import json

with open(r"scratch\cad_selection_5walls_d5.json", encoding="utf-8") as f:
    items = json.load(f)

for idx in [0, 1, 2, 8, 9, 10, 11, 12, 13, 14]:
    it = items[idx]
    print(f"[{idx}] Handle {it['handle']} | Type {it['type']} | Box: {it['box_rvt']}")
    if "pts_rvt" in it:
        for p in it["pts_rvt"]:
            print(f"    ({p[0]:.4f}, {p[1]:.4f})")
    if "start_rvt" in it:
        print(f"    Line: ({it['start_rvt'][0]:.4f}, {it['start_rvt'][1]:.4f}) -> ({it['end_rvt'][0]:.4f}, {it['end_rvt'][1]:.4f})")
