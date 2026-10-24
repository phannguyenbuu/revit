import json

with open(r'scratch/current_cad_selection.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

for it in items:
    if it.get('layer') == '32-CUA':
        print(f"Handle: {it['handle']} Type: {it['type']}")
        if it['type'] == 'AcDbPolyline':
            pts = it.get('points_rvt', [])
            print(f"  Pts: {[[round(p[0], 3), round(p[1], 3)] for p in pts]}")
        elif it['type'] == 'AcDbArc':
            print(f"  Bbox: {it.get('bbox_rvt')}")
