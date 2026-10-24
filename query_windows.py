import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

payload = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_FourWalls.dll',
    'typeName': 'RevitScript.InspectWindowsToModify',
    'methodName': 'Run'
}

req = urllib.request.Request('http://127.0.0.1:8090/api/execute', data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
res = urllib.request.urlopen(req, timeout=10)
raw = res.read().decode('utf-8')
data = json.loads(raw)
with open(r'd:\Dropbox\_Documents\RevitAI\inspect_windows.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print('Total windows found:', data.get('totalWindows'))
print('\nGrids:')
for g in data.get('grids', []):
    print(f"  {g['name']}: p1={g['p1']}, p2={g['p2']}")
