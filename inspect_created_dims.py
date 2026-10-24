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

new_ids = [2414006, 2414007, 2414008, 2414009, 2414010, 2414011, 2414012, 2414013, 2414014, 2414015, 2414016, 2414017, 2414018, 2414019]

for v in data.get('results', []):
    print(f"=== View: {v.get('viewName')} (ID {v.get('viewId')}) - Total Dims: {v.get('totalDims')} ===")
    dims = v.get('dims', [])
    for d in dims:
        if d.get('id') in new_ids:
            segs = d.get('segments', [])
            total_mm = sum(s.get('valMm', 0) for s in segs if s.get('valMm', 0) > 0)
            small = [s for s in segs if 0 < s.get('valMm', 9999) <= 200]
            zeros = [s for s in segs if s.get('valMm', 9999) == 0]
            print(f"Dim {d.get('id')}: Type='{d.get('dimType')}', Origin=({d.get('origin',{}).get('x')}, {d.get('origin',{}).get('y')}), Segments={len(segs)}, TotalLen={total_mm:.1f}mm, Small(<=200)={len(small)}, Zeros={len(zeros)}")
