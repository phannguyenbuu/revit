import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('inspect_all_window_fams.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

for fam in data.get('families', []):
    name = fam['name']
    if 'CUA SO' in name.upper() or 'ATT' in name.upper():
        print(f"Family: {name}")
        for form in fam.get('forms', []):
            print(f"  ID: {form['id']}, Type: {form.get('type')}, SubCat: {form.get('subCat')}, BB: {form.get('bb')}")
