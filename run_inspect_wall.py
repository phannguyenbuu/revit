import urllib.request
import json
import sys

if sys.stdout:
    sys.stdout.reconfigure(encoding='utf-8')

url = 'http://127.0.0.1:8090/api/execute'
p = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_FacadeWalls.dll',
    'typeName': 'RevitScript.InspectWall2369928',
    'methodName': 'Run'
}
req = urllib.request.Request(url, data=json.dumps(p).encode('utf-8'), headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req, timeout=30) as res:
    data = json.loads(res.read().decode('utf-8'))
    print("Element 2369928:", data.get("elem2369928"))
    print("Selection:", data.get("selection"))
    print("\nWalls count:", data.get("wallsCount"))
    for w in data.get("walls", []):
        print(f"  Wall ID {w['id']}: {w['name']}, Base: {w['baseLevel']} (+{w['baseOffset']:.0f}), Top: {w['topLevel']} (+{w['topOffset']:.0f}), H: {w['height']:.0f}, P0: {w['p0']}, P1: {w['p1']}, Z:[{w['minZ']:.0f}..{w['maxZ']:.0f}], Inserts: {w['inserts']}")
    print("\nWindows count:", data.get("windowsCount"))
    for wi in data.get("windows", []):
        print(f"  Window ID {wi['id']}: {wi['name']} ({wi['sym']}), Host: {wi['host']}, Z:[{wi['minZ']:.0f}..{wi['maxZ']:.0f}]")
