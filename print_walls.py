import urllib.request, json, sys
if sys.stdout: sys.stdout.reconfigure(encoding='utf-8')
url = 'http://127.0.0.1:8090/api/execute'
p = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_FindWalls.dll',
    'typeName': 'RevitScript.FindWallsAroundAxis1',
    'methodName': 'Run'
}
req = urllib.request.Request(url, data=json.dumps(p).encode('utf-8'), headers={'Content-Type': 'application/json'})
data = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
for w in data.get("walls", []):
    print(f"Wall {w['id']}: {w['name']}, Lvl: {w['level']}, Y:[{w['minY']:.0f}..{w['maxY']:.0f}], Z:[{w['minZ']:.0f}..{w['maxZ']:.0f}], Inserts: {w['inserts']}")
