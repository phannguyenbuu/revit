import urllib.request
import json
import sys

if sys.stdout:
    sys.stdout.reconfigure(encoding='utf-8')

url = 'http://127.0.0.1:8090/api/execute'
p = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_FacadeWalls.dll',
    'typeName': 'RevitScript.InspectBeamsOnAxis1',
    'methodName': 'Run'
}
req = urllib.request.Request(url, data=json.dumps(p).encode('utf-8'), headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req, timeout=30) as res:
    data = json.loads(res.read().decode('utf-8'))
    print("Beams count on Axis 1:", data.get("count"))
    for b in data.get("beams", []):
        print(f"ID {b['id']} | {b['sym']} | P0:{b['p0']} -> P1:{b['p1']} | Z:[{b['minZ']:.0f}..{b['maxZ']:.0f}] | zOff: {b['zOff']}")
