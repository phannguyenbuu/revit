import sys
import json

sys.stdout.reconfigure(encoding='utf-8')
data = json.load(open('detailed_elements.json', encoding='utf-8'))

for lvl_name in ['MẶT BẰNG TẦNG 2', 'MẶT BẰNG TẦNG 3']:
    walls = [w for w in data['walls'] if w['baseLevel'] == lvl_name]
    print(f"\nWalls at {lvl_name} (count {len(walls)}):")
    for w in sorted(walls, key=lambda x: (x['dir'], x['y0'], x['x0'])):
        print(f"  Wall {w['id']}: ({w['x0']}, {w['y0']}) -> ({w['x1']}, {w['y1']}) | dir={w['dir']}, name={w['name']}")
