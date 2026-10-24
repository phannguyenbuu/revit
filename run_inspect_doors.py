import revit_cli
import json
import urllib.request

base = revit_cli.get_base_url()
payload = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_DoorD7_v16.dll',
    'typeName': 'RevitScript.InspectFloorDoors',
    'methodName': 'Run'
}
req = urllib.request.Request(base + '/api/execute', data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
res = urllib.request.urlopen(req)
data = json.loads(res.read().decode())
doors = data.get('doors', [])
print(f"Total doors found: {len(doors)}")
for d in doors:
    print(f"ID {d.get('id')}: {d.get('name')} ('{d.get('symName')}'), Mark={d.get('mark')}, Loc=({d.get('x')}, {d.get('y')}), BB_X=[{d.get('bbMinX')}, {d.get('bbMaxX')}], Width={d.get('width')}mm")
