import sys
import json
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')
data = json.load(open('columns_data.json', encoding='utf-8'))

# Delete the duplicate column 2379808 from consideration
cols = [c for c in data['cols'] if c['id'] != 2379808]

by_x = defaultdict(list)
for c in cols:
    by_x[c['x']].append(c)

print(f"Total valid columns: {len(cols)}")
grid_points = {}
for x in sorted(by_x.keys()):
    row = by_x[x]
    y_dict = {c['y']: c for c in row}
    grid_points[x] = y_dict
    print(f"Trục X = {x}: Ys = {sorted(y_dict.keys())}")
