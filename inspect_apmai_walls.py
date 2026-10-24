import sys
import json

sys.stdout.reconfigure(encoding='utf-8')
data = json.load(open('detailed_elements.json', encoding='utf-8'))
apmai_walls = [w for w in data['walls'] if w['baseLevel']=='MẶT BẰNG TẦNG 1' and w['topLevel']=='MẶT BẰNG TẦNG ÁP MÁI']
print(f"Count: {len(apmai_walls)}")
for w in apmai_walls:
    print(f"Id: {w['id']} | Name: {w['name']} | ({w['x0']}, {w['y0']}) -> ({w['x1']}, {w['y1']})")
