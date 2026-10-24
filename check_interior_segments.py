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
    if v.get('viewId') == 312:
        for d in v.get('dims', []):
            if d.get('id') in [2416016, 2416017]:
                print(f"=== Dim {d.get('id')} (Orig={d.get('origin')}, Segs={d.get('numSegments')}) ===")
                vals = [s.get('valMm') for s in d.get('segments', [])]
                print("Segments:", vals)
                # Look for door widths: 1400, 1000, 1200, 800, 1300
                door_widths = [1400, 1000, 1200, 800, 1300]
                found_doors = [v for v in vals if v in door_widths]
                print("Door Width Segments Found:", found_doors)
