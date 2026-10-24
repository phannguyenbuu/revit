import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('inspect_fam_elements.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

print(f"Family: {data.get('familyName')}")
print(f"Forms Count: {data.get('formsCount')}")
for form in data.get('forms', []):
    print(f"ID: {form['id']}, Type: {form['type']}, SubCat: {form['subCat']}, BB: {form['bb']}")

print(f"\nNested Instances: {data.get('nested')}")
