import json

with open('etabs_beam_data.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

cols = d.get('columns', [])
mapping = {
    'C1': 'C1', 'C2': 'C2', 'C3': 'C3', 'C4': 'C4', 'C5': 'C5', 'C6': 'C6',
    'C10': 'C7', 'C11': 'C8', 'C12': 'C9', 'C13': 'C10', 'C14': 'C11',
    'C15': 'C12', 'C16': 'C13', 'C17': 'C14', 'C18': 'C15'
}

summary = {}
for c in cols:
    nl = mapping[c['label']]
    if nl not in summary:
        summary[nl] = {
            'old': c['label'],
            'sec': c.get('section'),
            'coord': (c['p1'][0], c['p1'][1]),
            'stories': set()
        }
    summary[nl]['stories'].add(c['story'])

for nl in sorted(summary.keys(), key=lambda x: int(x[1:])):
    s = summary[nl]
    print(f"{nl} (was {s['old']}): sec={s['sec']}, coord={s['coord']}, stories={sorted(list(s['stories']))}")
