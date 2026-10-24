import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('scan_all_dims.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for v in data.get('viewReports', []):
    print(f"View: {v['viewName']} (ID: {v['viewId']}) - Total: {v['totalDims']}, Zero: {v['dimsWithZero']}, ZerosInMiddle: {v['dimsWithZerosInMiddle']}")
    for d in v['dims']:
        if d['hasZero'] or d['hasZerosInMiddle']:
            print(f"  Dim ID {d['id']}: numSegs={d['numSegs']}, totalSpan={d['totalSpanMm']}, origin=({d['origin']['x']}, {d['origin']['y']}), dir=({d['dir']['x']}, {d['dir']['y']})")
            print(f"    segVals: {d['segVals']}")
