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

for vr in data.get('viewReports', []):
    if vr.get('viewId') == 312:
        for d in vr.get('dims', []):
            if d.get('totalSpanMm') == 14900: # West/East L1 or L2
                print(f"Dim {d.get('id')}: Dir={d.get('dir')}, SegVals={d.get('segVals')}")
