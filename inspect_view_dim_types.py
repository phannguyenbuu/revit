import revit_cli
import json
import urllib.request

base = revit_cli.get_base_url()

# Let's inspect all dims on view 312
payload = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_DoorD7_v16.dll',
    'typeName': 'RevitScript.InspectAllDimensionsDetailed',
    'methodName': 'Run',
    'args': {'viewId': 312}
}
req = urllib.request.Request(base + '/api/execute', data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
res = urllib.request.urlopen(req)
data = json.loads(res.read().decode())

for v in data.get('results', []):
    if v.get('viewId') == 312:
        for d in v.get('dims', []):
            print(f"Dim {d.get('id')}: typeId={d.get('typeId', 'N/A')}, typeName='{d.get('dimType')}'")
