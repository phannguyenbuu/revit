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

walls_by_level = {}
for w in data.get('walls', []):
    lvl = w['level']
    if lvl not in walls_by_level:
        walls_by_level[lvl] = []
    walls_by_level[lvl].append(w)

for lvl, wlist in walls_by_level.items():
    print(f"\n==================== {lvl} (Count: {len(wlist)}) ====================")
    for w in sorted(wlist, key=lambda x: (x['p0'], x['p1'])):
        ins_str = f" | Inserts: {len(w['inserts'])} ({', '.join(w['inserts'])})" if w['inserts'] else ""
        print(f"  ID {w['id']} | {w['name']} | P0:{w['p0']} -> P1:{w['p1']} | H={w['height']:.0f}{ins_str}")
