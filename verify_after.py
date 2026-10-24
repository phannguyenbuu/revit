import sys
import json
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')
data = json.load(open('detailed_elements_after.json', encoding='utf-8'))

beams = data['beams']
print(f"Total beams in Revit: {len(beams)}")
by_lvl = defaultdict(int)
for b in beams:
    by_lvl[b['level']] += 1
for lvl, cnt in sorted(by_lvl.items()):
    print(f"  {lvl}: {cnt} beams")

walls = data['walls']
print(f"\nTotal walls in Revit: {len(walls)}")
by_base = defaultdict(list)
for w in walls:
    by_base[w['baseLevel']].append(w)

for base, wlist in sorted(by_base.items(), key=lambda x: str(x[0])):
    print(f"\nBase: {base} ({len(wlist)} walls):")
    by_off = defaultdict(int)
    for w in wlist:
        by_off[w['topOffMm']] += 1
    for off, cnt in sorted(by_off.items()):
        print(f"   Top Offset = {off}mm: {cnt} walls")
