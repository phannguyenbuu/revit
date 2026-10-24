import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open(r'd:\Dropbox\_Documents\RevitAI\inspect_windows.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

windows = data.get('windows', [])

# Grid coordinates
# Grid A: Y = 0.0
# Grid D: Y = 13.20
# Grid 2: X = 4.35
# Grid 10: X = 33.35

matches = []
non_matches = []

for w in windows:
    x = w['x']
    y = w['y']
    z = w['z']
    
    # Check if along Grid A (Y ~ 0) or Grid D (Y ~ 13.2)
    is_axis_A = abs(y - 0.0) < 0.6
    is_axis_D = abs(y - 13.2) < 0.6
    
    # Check if between Grid 2 (4.35) and Grid 10 (33.35)
    in_range_x = (x >= 4.0 and x <= 33.6)
    
    if (is_axis_A or is_axis_D) and in_range_x:
        axis_name = 'Trục A' if is_axis_A else 'Trục D'
        matches.append((axis_name, w))
    else:
        non_matches.append(w)

print(f"Total matching windows: {len(matches)}")
print(f"Total non-matching windows: {len(non_matches)}\n")

# Group by Axis and Level
from collections import defaultdict
grouped = defaultdict(list)
for axis, w in matches:
    grouped[(axis, w['level'])].append(w)

for (axis, lvl), win_list in sorted(grouped.items()):
    print(f"=== {axis} | {lvl} (Count: {len(win_list)}) ===")
    for w in win_list:
        print(f"  ID: {w['id']} | Symbol: {w['symbolName']} | Family: {w['familyName']} | X={w['x']}, Y={w['y']}, Z={w['z']} | Sill={w['sill_mm']}mm, Height={w['height_mm']}mm (TypeParam={w['heightIsType']})")
