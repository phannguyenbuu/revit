import sys
import json

sys.stdout.reconfigure(encoding='utf-8')
data = json.load(open('detailed_elements.json', encoding='utf-8'))

# Walls with base = Tầng 4
t4_walls = [w for w in data['walls'] if w['baseLevel'] == 'MẶT BẰNG TẦNG 4']
print(f"Walls at Tầng 4 (count {len(t4_walls)}):")
for w in t4_walls:
    print(f"  Wall {w['id']}: ({w['x0']}, {w['y0']}) -> ({w['x1']}, {w['y1']}) | dir={w['dir']}, name={w['name']}")

tum_walls = [w for w in data['walls'] if w['baseLevel'] == 'MẶT BẰNG TẦNG TUM']
print(f"\nWalls at Tầng Tum (count {len(tum_walls)}):")
for w in tum_walls:
    print(f"  Wall {w['id']}: ({w['x0']}, {w['y0']}) -> ({w['x1']}, {w['y1']}) | dir={w['dir']}, name={w['name']}")
