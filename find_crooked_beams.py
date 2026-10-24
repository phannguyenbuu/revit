import sys
import json

sys.stdout.reconfigure(encoding='utf-8')
data = json.load(open('detailed_elements_after.json', encoding='utf-8'))

crooked = []
for b in data['beams']:
    dx = abs(b['p1x'] - b['p0x'])
    dy = abs(b['p1y'] - b['p0y'])
    # If a beam is straight, either dx == 0 (strictly Y direction) or dy == 0 (strictly X direction)
    if dx > 10 and dy > 10:
        crooked.append(b)

print(f"Total crooked beams: {len(crooked)}")
for b in crooked:
    print(f"Beam {b['id']}: ({b['p0x']}, {b['p0y']}) -> ({b['p1x']}, {b['p1y']}) | Name: {b['name']}")
