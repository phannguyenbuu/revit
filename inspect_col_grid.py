import sys
import json
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')
data = json.load(open('columns_data.json', encoding='utf-8'))
cols = data['cols']

by_x = defaultdict(list)
for c in cols:
    by_x[c['x']].append(c)

print(f"Total columns: {len(cols)}")
for x in sorted(by_x.keys()):
    row = by_x[x]
    y_info = [f"Y={c['y']} ({c['name']}, top={c['topLevel']})" for c in sorted(row, key=lambda i: i['y'])]
    print(f"Trục X={x} (count {len(row)}):")
    for yi in y_info:
        print(f"   {yi}")
