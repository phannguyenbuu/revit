import json
from collections import Counter

with open(r"D:\Dropbox\_Documents\RevitAI\scratch\selection_3walls_1window.json", "r", encoding="utf-8") as f:
    items = json.load(f)

print(f"Total items: {len(items)}")
layers = Counter(it['layer'] for it in items)
types = Counter(it['type'] for it in items)
print("Layers:", dict(layers))
print("Types:", dict(types))

for i, it in enumerate(items):
    t = it['type']
    l = it['layer']
    h = it['handle']
    bx = it.get('bbox_rvt', {})
    min_p = bx.get('min', [0, 0])
    max_p = bx.get('max', [0, 0])
    dx = max_p[0] - min_p[0]
    dy = max_p[1] - min_p[1]
    extra = ""
    if t == "AcDbBlockReference":
        extra = f"Block: {it.get('block_name')}, Ins: {it.get('ins_rvt')}"
    elif t == "AcDbLine":
        extra = f"Line: ({it['start_rvt'][0]:.3f}, {it['start_rvt'][1]:.3f}) -> ({it['end_rvt'][0]:.3f}, {it['end_rvt'][1]:.3f})"
    elif t == "AcDbPolyline":
        pts = it.get('points_rvt', [])
        extra = f"Pline ({len(pts)} pts, closed={it.get('closed')}): " + " -> ".join(f"({p[0]:.3f}, {p[1]:.3f})" for p in pts)
    print(f"[{i:2d}] {t:18s} | Layer: {l:12s} | Handle: {h:7s} | Size: ({dx:.3f} x {dy:.3f}) | {extra}")
