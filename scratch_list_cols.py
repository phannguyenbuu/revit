import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

p = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_CreateTumSlabWithHole.dll',
    'typeName': 'RevitScript.InspectAllColumnsStructure',
    'methodName': 'Run'
}
req = urllib.request.Request('http://127.0.0.1:8090/api/execute', data=json.dumps(p).encode('utf-8'), headers={'Content-Type': 'application/json'})
resp = json.loads(urllib.request.urlopen(req, timeout=10).read().decode('utf-8'))
cols = resp.get('cols', [])
print(f'Total: {len(cols)}')
for c in sorted(cols, key=lambda x: (x['x'], x['y'])):
    print(f"ID: {c['id']}, Type: {c['name']}, X: {c['x']}, Y: {c['y']}, Base: {c['baseLevel']}, Top: {c['topLevel']}, TopElev: {c['topElevM']}, TopOffset: {c['topOffsetMm']}")
