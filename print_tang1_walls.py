import urllib.request
import json
import sys

if sys.stdout:
    sys.stdout.reconfigure(encoding='utf-8')

url = 'http://127.0.0.1:8090/api/execute'
p = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_FacadeWalls.dll',
    'typeName': 'RevitScript.ListAllProjectWalls',
    'methodName': 'Run'
}
req = urllib.request.Request(url, data=json.dumps(p).encode('utf-8'), headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req, timeout=30) as res:
    data = json.loads(res.read().decode('utf-8'))

for w in data.get('walls', []):
    if 'TẦNG 1' in w['level']:
        ins_str = f" | Inserts: {len(w['inserts'])} ({', '.join(w['inserts'])})" if w['inserts'] else ""
        print(f"ID {w['id']} | {w['name']} | P0:{w['p0']} -> P1:{w['p1']} | H={w['height']:.0f}{ins_str}")
