import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('inspect_windows.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('--- All windows in inspect_windows.json ---')
for w in data.get('windows', []):
    y = w['y']
    x = w['x']
    if 1.0 < y < 12.0:
        print(f"ID: {w['id']}, Level: {w['level']}, Symbol: {w['symbolName']}, Family: {w['familyName']}, X: {x}, Y: {y}, Z: {w['z']}")
