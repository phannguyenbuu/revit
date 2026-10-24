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
    print("Total walls:", data.get("count"))
    for w in data.get("walls", []):
        if 2369920 <= w['id'] <= 2369940:
            print(f"ID {w['id']} | {w['name']} | Lvl: {w['level']} | X:[{w['minX']:.0f}..{w['maxX']:.0f}] Y:[{w['minY']:.0f}..{w['maxY']:.0f}] Z:[{w['minZ']:.0f}..{w['maxZ']:.0f}] | Inserts: {w['inserts']}")
