import urllib.request
import json
import sys

if sys.stdout:
    sys.stdout.reconfigure(encoding='utf-8')

url = 'http://127.0.0.1:8090/api/execute'
p = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_FacadeWalls.dll',
    'typeName': 'RevitScript.InspectAllBeams',
    'methodName': 'Run'
}
req = urllib.request.Request(url, data=json.dumps(p).encode('utf-8'), headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req, timeout=30) as res:
    data = json.loads(res.read().decode('utf-8'))
    print("Total beams:", data.get("totalBeams"))
    print("Level groups:", data.get("levelGroups"))
    print("\nSample beams:")
    for b in data.get("sample", []):
        print(f"  ID {b['id']} | {b['name']} ({b['sym']}) | Level: {b['level']} | zJust: {b['zJust']} | zOff: {b['zOffsetMm']:.1f} | minZ: {b['minZ']:.0f} | maxZ: {b['maxZ']:.0f}")
