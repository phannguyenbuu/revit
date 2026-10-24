import urllib.request
import json

payload = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_FourWalls.dll',
    'typeName': 'RevitScript.InspectGridsAndColumns',
    'methodName': 'Run'
}
req = urllib.request.Request('http://127.0.0.1:8090/api/execute', data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
res = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
for g in res.get('grids', []):
    if g['name'] in ['1', '2', 'A', 'B']:
        print(f"Grid {g['name']}: p1={g['p1']}, p2={g['p2']}")
