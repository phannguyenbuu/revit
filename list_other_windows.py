import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open(r'd:\Dropbox\_Documents\RevitAI\inspect_windows.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Windows outside target range:")
for w in data.get('windows', []):
    x, y, z = w['x'], w['y'], w['z']
    is_axis_A = abs(y - 0.0) < 0.6
    is_axis_D = abs(y - 13.2) < 0.6
    in_range_x = (x >= 4.0 and x <= 33.6)
    if not ((is_axis_A or is_axis_D) and in_range_x):
        print(f"  ID: {w['id']} | {w['symbolName']} | X={x}, Y={y}, Z={z} | Level={w['level']}")
