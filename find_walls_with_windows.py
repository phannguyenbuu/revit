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
    
walls_with_windows = []
for w in data.get('walls', []):
    win_inserts = [ins for ins in w.get('inserts', []) if 'Windows' in ins]
    if win_inserts:
        walls_with_windows.append((w, win_inserts))

print(f"Total walls with windows: {len(walls_with_windows)}")
for w, wins in walls_with_windows:
    print(f"\nWall ID {w['id']} | Level: {w['level']} | H={w['height']:.0f}mm | P0={w['p0']} -> P1={w['p1']}")
    print(f"  X:[{w['minX']:.0f}..{w['maxX']:.0f}] Y:[{w['minY']:.0f}..{w['maxY']:.0f}] Z:[{w['minZ']:.0f}..{w['maxZ']:.0f}]")
    for win in wins:
        print(f"    - {win}")
