import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('inspect_dims_output.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

v1 = data['results'][0]
print(f"VIEW: {v1['viewName']} (ID: {v1['viewId']})")
for d in v1['dims']:
    segs_vals = [s['valMm'] for s in d['segments']]
    has_z = d['hasZero']
    print(f"ID {d['id']}: numSegs={d['numSegments']}, origin=({d['origin']['x']}, {d['origin']['y']}), dir=({d['dir']['x']}, {d['dir']['y']}), hasZero={has_z}")
    if has_z or d['numSegments'] > 0:
        print(f"   vals: {segs_vals}")
