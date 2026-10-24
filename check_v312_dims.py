import revit_cli
import json
import urllib.request

base = revit_cli.get_base_url()
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
    print(f"View {v.get('viewName')} (ID {v.get('viewId')}) has {v.get('totalDims')} dims")
    for d in v.get('dims', []):
        print(f"  ID {d.get('id')}: Orig={d.get('origin')}, Type={d.get('dimType')}")
