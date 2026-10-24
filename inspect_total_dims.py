import revit_cli
import json
import urllib.request

base = revit_cli.get_base_url()
payload = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_DoorD7_v16.dll',
    'typeName': 'RevitScript.ScanAllViewsDimensions',
    'methodName': 'Run'
}
req = urllib.request.Request(base + '/api/execute', data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
res = urllib.request.urlopen(req)
data = json.loads(res.read().decode())
total = sum(v.get('totalDims', 0) for v in data.get('viewReports', []))
print(f"Total dims across floor views: {total}")
for v in data.get('viewReports', []):
    if v.get('totalDims', 0) > 0:
        print(f"  - View '{v.get('viewName')}' (ID {v.get('viewId')}): {v.get('totalDims')} dims")
