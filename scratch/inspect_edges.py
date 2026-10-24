import json

with open(r'D:\Dropbox\_Documents\RevitAI\scratch\cad_selection_12walls_actual.json', encoding='utf-8') as f:
    items = json.load(f)

print(f"Total items in selection: {len(items)}")
for i, it in enumerate(items):
    print(f"\n--- Item {i}: {it['type']}, Layer: {it['layer']}, Handle: {it['handle']}, Closed: {it.get('closed')} ---")
    pts = it.get('pts_rvt', [])
    for j in range(len(pts)):
        p1 = pts[j]
        p2 = pts[(j + 1) % len(pts)]
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        length = (dx**2 + dy**2)**0.5
        print(f"  Edge {j}: ({p1[0]:.3f}, {p1[1]:.3f}) -> ({p2[0]:.3f}, {p2[1]:.3f}) | len={length:.3f}m | dx={dx:.3f}, dy={dy:.3f}")
