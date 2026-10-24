import sys
import urllib.request
import json

sys.stdout.reconfigure(encoding='utf-8')

req = urllib.request.Request('http://127.0.0.1:8090/api/execute', data=json.dumps({
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_CreateTumSlabWithHole.dll',
    'typeName': 'RevitScript.InspectAllColumnsStructure',
    'methodName': 'Run'
}).encode('utf-8'), headers={'Content-Type': 'application/json'})

with urllib.request.urlopen(req) as res:
    data = json.loads(res.read().decode('utf-8'))
    cols = data.get('cols', [])
    l4_cols = [c for c in cols if '4' in c['baseLevel']]
    tum_cols = [c for c in cols if 'TUM' in c['baseLevel']]
    print(f"L4 cols ({len(l4_cols)}):")
    for c in l4_cols:
        print(f"  ID: {c['id']}, X: {c['x']}, Y: {c['y']}, Name: {c['name']}, Top: {c['topLevel']}, Off: {c['topOffsetMm']}")
    print(f"Tum cols ({len(tum_cols)}):")
    for c in tum_cols:
        print(f"  ID: {c['id']}, X: {c['x']}, Y: {c['y']}, Name: {c['name']}, Top: {c['topLevel']}, Off: {c['topOffsetMm']}")
