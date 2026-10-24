import json

with open(r"D:\Dropbox\_Documents\RevitAI\scratch\current_cad_selection.json", "r", encoding="utf-8") as f:
    items = json.load(f)

for i, it in enumerate(items):
    print(f"\n================ Item {i} ================")
    print(f"Handle: {it['handle']}, Type: {it['type']}, Layer: {it['layer']}, Closed: {it.get('closed')}")
    print(f"BBox RVT: {it['bbox_rvt']}")
    pts = it.get('points_rvt', [])
    for j in range(len(pts) - (0 if it.get('closed') else 1)):
        p1 = pts[j]
        p2 = pts[(j + 1) % len(pts)]
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        length = (dx**2 + dy**2)**0.5
        print(f"  Segment {j}: ({p1[0]:.3f}, {p1[1]:.3f}) -> ({p2[0]:.3f}, {p2[1]:.3f}) | len={length:.3f}m | dx={dx:.3f}, dy={dy:.3f}")
