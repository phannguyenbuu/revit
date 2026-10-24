import json

with open(r'scratch/current_cad_selection.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

for it in items:
    if it.get('handle') in ['44C233', '44C244']:
        print(json.dumps(it, indent=2))
