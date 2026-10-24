import sys
import json

sys.stdout.reconfigure(encoding='utf-8')
data = json.load(open('detailed_elements_straight.json', encoding='utf-8'))
crooked = [b for b in data['beams'] if abs(b['p1x']-b['p0x']) > 10 and abs(b['p1y']-b['p0y']) > 10]
print(f"Total beams in Revit: {len(data['beams'])}")
print(f"Crooked beams: {len(crooked)}")
for b in crooked:
    print(f"  {b['id']}: ({b['p0x']}, {b['p0y']}) -> ({b['p1x']}, {b['p1y']})")
