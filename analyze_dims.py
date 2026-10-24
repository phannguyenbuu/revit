import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('inspect_dims_output.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for v in data['results']:
    print(f"\n==========================================")
    print(f"VIEW: {v['viewName']} (ID: {v['viewId']})")
    print(f"==========================================")
    for d in v['dims']:
        segs_vals = [s['valMm'] for s in d['segments']]
        has_z = d['hasZero']
        print(f"ID {d['id']}: numSegs={d['numSegments']}, origin=({d['origin']['x']}, {d['origin']['y']}), dir=({d['dir']['x']}, {d['dir']['y']}), hasZero={has_z}")
        if has_z or d['numSegments'] > 0:
            print(f"   vals: {segs_vals}")
