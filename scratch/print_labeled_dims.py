import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('dump_fam_dimensions.json', 'r', encoding='utf-8-sig') as f:
    d = json.load(f)

for dim in d.get('dims', []):
    if dim.get('label'):
        print(f"ID: {dim['id']}, Label: {dim['label']}, Val: {dim['val']}")
