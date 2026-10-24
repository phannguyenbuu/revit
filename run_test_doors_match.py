import revit_cli
import json
import urllib.request

base = revit_cli.get_base_url()
payload = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_DoorD7_v16.dll',
    'typeName': 'RevitScript.TestBuildInteriorChainsWithDoors',
    'methodName': 'Run'
}
req = urllib.request.Request(base + '/api/execute', data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
res = urllib.request.urlopen(req)
data = json.loads(res.read().decode())
print("=== AB Door Matches ===")
for m in data.get('abDoorMatches', []):
    print(f"  Target {m['target']}: Matched={m['matched']}")
print("=== CD Door Matches ===")
for m in data.get('cdDoorMatches', []):
    print(f"  Target {m['target']}: Matched={m['matched']}")
