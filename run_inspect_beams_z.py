import sys
import urllib.request
import json

sys.stdout.reconfigure(encoding='utf-8')

payload = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_CreateTumSlabWithHole.dll',
    'typeName': 'RevitScript.InspectBeamsZ',
    'methodName': 'Run'
}

req = urllib.request.Request(
    'http://127.0.0.1:8090/api/execute',
    data=json.dumps(payload).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)

try:
    with urllib.request.urlopen(req, timeout=60) as res:
        data = json.loads(res.read().decode('utf-8'))
        print(f"Total Beams: {data.get('totalBeams')}")
        for g in data.get('grouped', []):
            print(f"Level: {g['level']}, Count: {g['count']}, LevelElev: {g['levelElevM']}m, Beam Z: {g['z0M']}, Offsets: {g['p0OffMm']}")
except Exception as ex:
    print(f"Error calling bridge: {ex}")
