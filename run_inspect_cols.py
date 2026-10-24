import urllib.request
import json
import sys

if sys.stdout:
    sys.stdout.reconfigure(encoding='utf-8')

url = 'http://127.0.0.1:8090/api/execute'
p = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_FacadeWalls.dll',
    'typeName': 'RevitScript.InspectAxis1Cols',
    'methodName': 'Run'
}
req = urllib.request.Request(url, data=json.dumps(p).encode('utf-8'), headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req, timeout=30) as res:
    data = json.loads(res.read().decode('utf-8'))
    print("Columns count on Axis 1:", data.get("count"))
    for c in data.get("cols", []):
        print(f"ID {c['id']} | {c['name']} | Pt: {c['pt']} | Base: {c['baseLevel']} -> Top: {c['topLevel']} (off={c['topOffset']:.0f}) | Z:[{c['minZ']:.0f}..{c['maxZ']:.0f}]")
