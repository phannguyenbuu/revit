import urllib.request
import json

req = urllib.request.Request('http://127.0.0.1:8090/api/execute', data=json.dumps({
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_CreateTumSlabWithHole.dll',
    'typeName': 'RevitScript.InspectAllColumnsStructure',
    'methodName': 'Run'
}).encode('utf-8'), headers={'Content-Type': 'application/json'})

with urllib.request.urlopen(req) as res:
    data = json.loads(res.read().decode('utf-8'))
    cols = data.get('cols', [])
    print(f"Total cols: {len(cols)}")
    l1_cols = [c for c in cols if c['baseLevel'] == 'MẶT BẰNG TẦNG 1']
    print(f"L1 cols: {len(l1_cols)}")
    for c in l1_cols:
        print(f"ID: {c['id']}, X: {c['x']}, Y: {c['y']}, Name: {c['name']}")
