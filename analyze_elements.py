import sys
import json
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')
data = json.load(open('detailed_elements.json', encoding='utf-8'))

print("=== FLOORS ===")
for f in data['floors']:
    print(f"Floor {f['id']}: {f['name']} | Level: {f['level']} (elev: {f['elevM']}m) | X: [{f['minX']}..{f['maxX']}], Y: [{f['minY']}..{f['maxY']}], Z: [{f['minZ']}..{f['maxZ']}]")

print("\n=== EXISTING BEAMS ===")
for b in data['beams']:
    print(f"Beam {b['id']}: {b['name']} | Level: {b['level']} | Line: ({b['p0x']}, {b['p0y']}) -> ({b['p1x']}, {b['p1y']})")

print(f"\n=== WALLS TOTAL: {data['wallsCount']} ===")
by_base = defaultdict(list)
for w in data['walls']:
    by_base[w['baseLevel']].append(w)

for base, wlist in sorted(by_base.items(), key=lambda x: str(x[0])):
    print(f"\nBase Level: {base} ({len(wlist)} walls):")
    # Group by top level
    by_top = defaultdict(list)
    for w in wlist:
        by_top[w['topLevel']].append(w)
    for top, twlist in sorted(by_top.items(), key=lambda x: str(x[0])):
        dirs = defaultdict(int)
        for w in twlist:
            dirs[w['dir']] += 1
        offsets = set(w['topOffMm'] for w in twlist)
        print(f"   Top: {top} ({len(twlist)} walls) | Dirs: {dict(dirs)} | Top Offsets: {offsets}")
