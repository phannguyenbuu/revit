import urllib.request
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

p = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_Sync.dll',
    'typeName': 'RevitScript.ListAllProjectWalls',
    'methodName': 'Run'
}
req = urllib.request.Request('http://127.0.0.1:8092/api/execute', data=json.dumps(p).encode('utf-8'), headers={'Content-Type': 'application/json'})
raw = urllib.request.urlopen(req, timeout=5).read().decode('utf-8')
res = json.loads(raw)
print(f"Total walls: {res['count']}")
for w in res['walls']:
    if '23788' in str(w['id']):
        print(f"ID: {w['id']} | {w['name']} | Base: {w['baseLvl']} (off: {w['baseOffset']}) | Top: {w['topLvl']} (off: {w['topOffset']}) | H: {w['h']} | Curve: {w['curve']}")
