import revit_cli
import json
import urllib.request

base = revit_cli.get_base_url()
payload = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_DoorD7_v16.dll',
    'typeName': 'RevitScript.InspectDoorReferences',
    'methodName': 'Run'
}
req = urllib.request.Request(base + '/api/execute', data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
res = urllib.request.urlopen(req)
data = json.loads(res.read().decode())
for item in data.get('results', []):
    print(f"=== Door {item.get('doorId')} ({item.get('doorName')}) ===")
    print("  Door Faces:", [f['x'] for f in item.get('doorFaces', [])])
    print("  Host Wall Faces:", [f['x'] for f in item.get('hostWallFaces', [])])
