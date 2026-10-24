import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open(r'd:\Dropbox\_Documents\RevitAI\inspect_windows.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

windows = data.get('windows', [])

# Grid 2: X = 4.35
# Grid 10: X = 33.35
# Grid A: Y = 0.0
# Grid D: Y = 13.20

a_wins = []
d_wins = []

for w in windows:
    x = w['x']
    y = w['y']
    # Check if between Grid 2 and Grid 10 (X in [4.0, 33.6])
    if not (4.0 <= x <= 33.6):
        continue
    
    if abs(y - 0.0) < 0.6:
        a_wins.append(w)
    elif abs(y - 13.2) < 0.6:
        d_wins.append(w)

print(f"=== TRỤC A (Total: {len(a_wins)}) ===")
for w in sorted(a_wins, key=lambda item: (item['levelElev_m'], item['x'])):
    print(f"  {w['level']} | ID: {w['id']} | X={w['x']:6.2f} | {w['symbolName']} | Sill={w['sill_mm']}mm")

print(f"\n=== TRỤC D (Total: {len(d_wins)}) ===")
for w in sorted(d_wins, key=lambda item: (item['levelElev_m'], item['x'])):
    print(f"  {w['level']} | ID: {w['id']} | X={w['x']:6.2f} | {w['symbolName']} | Sill={w['sill_mm']}mm")
