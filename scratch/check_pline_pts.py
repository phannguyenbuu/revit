import json

with open(r'scratch/current_cad_selection.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

for it in items:
    if it.get('handle') in ['44C233', '44C244']:
        print(f"Handle: {it['handle']}")
        pts = it.get('points_rvt', [])
        for i, p in enumerate(pts):
            print(f"  P{i}: ({p[0]:.4f}, {p[1]:.4f})")
