import sys
import json

sys.stdout.reconfigure(encoding='utf-8')
data = json.load(open('detailed_elements.json', encoding='utf-8'))

# Grids:
# A: Y = 0
# B: Y = 5400
# C: Y = 7800
# D: Y = 13200
# E: Y = 14900

# Let's inspect where walls are located along Y:
walls = data['walls']
y_wall_vals = sorted(list(set(w['y0'] for w in walls if w['dir'] == 'X')))
print("Y coordinates of X-direction walls:")
for y in y_wall_vals:
    matching = [w for w in walls if w['dir'] == 'X' and abs(w['y0'] - y) < 1]
    print(f"  Y = {y} ({len(matching)} walls)")

x_wall_vals = sorted(list(set(w['x0'] for w in walls if w['dir'] == 'Y')))
print("\nX coordinates of Y-direction walls:")
for x in x_wall_vals:
    matching = [w for w in walls if w['dir'] == 'Y' and abs(w['x0'] - x) < 1]
    print(f"  X = {x} ({len(matching)} walls)")
