import json

with open(r"D:\Dropbox\_Documents\RevitAI\scratch\handles_21_dump.json", "r", encoding="utf-8") as f:
    items = json.load(f)

for it in items:
    h = it['handle']
    t = it['type']
    print(f"--- Handle {h} ({t}) ---")
    if t == "AcDbLine":
        s = it['start_rvt']
        e = it['end_rvt']
        print(f"  Line: ({s[0]:.3f}, {s[1]:.3f}) -> ({e[0]:.3f}, {e[1]:.3f})")
    elif t == "AcDbPolyline":
        pts = it['points_rvt']
        closed = it['closed']
        for j in range(len(pts) - (0 if closed else 1)):
            p1 = pts[j]
            p2 = pts[(j + 1) % len(pts)]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            l = (dx*dx + dy*dy)**0.5
            print(f"  Seg {j}: ({p1[0]:.3f}, {p1[1]:.3f}) -> ({p2[0]:.3f}, {p2[1]:.3f}) L={l:.3f}")
