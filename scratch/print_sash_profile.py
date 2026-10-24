import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('inspect_sash_profile.json', 'r', encoding='utf-8-sig') as f:
    d = json.load(f)

for ext in d.get('extrusions', []):
    print(f"ID: {ext['id']}, SubCat: {ext['subCat']}, BB: {ext['bb']}, LoopCount: {ext['loopCount']}")
    for i, loop in enumerate(ext.get('loops', [])):
        print(f"  Loop {i}: {loop['bounds']}")
