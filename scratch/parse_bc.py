import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('inspect_bc_full.json', 'r', encoding='utf-8-sig') as f:
    text = f.read()

data = json.loads(text)

print(f"Total windows in model: {data.get('totalWindows')}")

print('\n=== Windows near B (Y ~ 5.4m) ===')
b_wins = [w for w in data.get('windows', []) if w.get('isNearB')]
for w in b_wins:
    print(f"ID: {w['id']} | Level: {w['level']} | Sym: {w['symbol']} | X: {w['x']}, Y: {w['y']}, Z: {w['z']} | Sill: {w['sill_mm']}, Head: {w['head_mm']}")
print(f"Total near B: {len(b_wins)}")

print('\n=== Windows near C (Y ~ 7.8m) ===')
c_wins = [w for w in data.get('windows', []) if w.get('isNearC')]
for w in c_wins:
    print(f"ID: {w['id']} | Level: {w['level']} | Sym: {w['symbol']} | X: {w['x']}, Y: {w['y']}, Z: {w['z']} | Sill: {w['sill_mm']}, Head: {w['head_mm']}")
print(f"Total near C: {len(c_wins)}")

print('\n=== Any Windows between Y = 1.0 and Y = 12.0 ===')
mid_wins = [w for w in data.get('windows', []) if 1.0 < w.get('y', 0) < 12.0]
for w in mid_wins:
    print(f"ID: {w['id']} | Level: {w['level']} | Sym: {w['symbol']} | X: {w['x']}, Y: {w['y']}, Z: {w['z']} | Sill: {w['sill_mm']}, Head: {w['head_mm']}")
print(f"Total intermediate Y: {len(mid_wins)}")

print(f"\n=== Walls near B (Y ~ 5.4m) - Count: {len(data.get('wallsNearB', []))} ===")
for wall in data.get('wallsNearB', []):
    print(f"ID: {wall['id']} | Level: {wall['level']} | Name: {wall['name']} | ({wall['start']['x']}, {wall['start']['y']}) -> ({wall['end']['x']}, {wall['end']['y']})")

print(f"\n=== Walls near C (Y ~ 7.8m) - Count: {len(data.get('wallsNearC', []))} ===")
for wall in data.get('wallsNearC', []):
    print(f"ID: {wall['id']} | Level: {wall['level']} | Name: {wall['name']} | ({wall['start']['x']}, {wall['start']['y']}) -> ({wall['end']['x']}, {wall['end']['y']})")
