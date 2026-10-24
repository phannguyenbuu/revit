import json

with open(r"D:\Dropbox\_Documents\RevitAI\scratch\handles_21_dump.json", "r", encoding="utf-8") as f:
    items = json.load(f)

print(f"Total items dumped: {len(items)}")

for i, it in enumerate(items):
    h = it['handle']
    if 'error' in it:
        print(f"[{i:2d}] Handle: {h} ERROR: {it['error']}")
        continue
    t = it['type']
    l = it['layer']
    bx = it.get('bbox_rvt', {})
    min_p = bx.get('min', [0, 0])
    max_p = bx.get('max', [0, 0])
    dx = max_p[0] - min_p[0]
    dy = max_p[1] - min_p[1]
    
    desc = ""
    if t == "AcDbLine":
        s = it['start_rvt']
        e = it['end_rvt']
        desc = f"Line: ({s[0]:.3f}, {s[1]:.3f}) -> ({e[0]:.3f}, {e[1]:.3f}) len={((e[0]-s[0])**2 + (e[1]-s[1])**2)**0.5:.3f}"
    elif t == "AcDbPolyline":
        pts = it.get('points_rvt', [])
        closed = it.get('closed', False)
        pt_strs = [f"({p[0]:.3f}, {p[1]:.3f})" for p in pts]
        desc = f"Pline ({len(pts)} pts, closed={closed}): " + " -> ".join(pt_strs)
    
    print(f"[{i:2d}] Handle: {h:7s} | Layer: {l:12s} | Type: {t:14s} | Bounds: [({min_p[0]:.3f}, {min_p[1]:.3f}) to ({max_p[0]:.3f}, {max_p[1]:.3f})] Size: ({dx:.3f} x {dy:.3f})\n     {desc}")
