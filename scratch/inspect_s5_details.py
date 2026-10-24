import json

with open(r"scratch\cad_selection_analyzed.json", encoding="utf-8") as f:
    data = json.load(f)

for it in data["items"]:
    if it["layer"] == "S5":
        print(f"Handle: {it['handle']} | Type: {it['type']} | Closed: {it.get('closed')}")
        print(f"  Box CAD: {it['box_cad']}")
        print(f"  Box RVT: {it['box_rvt']}")
        if "pts_rvt" in it:
            pts_str = " -> ".join([f"({p[0]:.3f}, {p[1]:.3f})" for p in it["pts_rvt"]])
            print(f"  Vertices: {pts_str}")
        print()
