import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# 1. Inspect selection
payload_sel = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_DoorD7_v16.dll',
    'typeName': 'RevitScript.InspectCurrentSelectionNow',
    'methodName': 'Run'
}
req = urllib.request.Request('http://127.0.0.1:8090/api/execute', data=json.dumps(payload_sel).encode(), headers={'Content-Type': 'application/json'})
res = urllib.request.urlopen(req)
sel_data = json.loads(res.read().decode())

print("=== SELECTION ===")
print("Active View:", sel_data.get('activeViewName'), "ID:", sel_data.get('activeViewId'))
active_view_id = sel_data.get('activeViewId')

for item in sel_data.get('items', []):
    dim = item.get('dimInfo', {})
    segs = dim.get('segments', [])
    values = [s.get('value') for s in segs]
    texts = [s.get('text') for s in segs]
    print(f"\nDim ID {item.get('id')}: {len(segs)} segments")
    print("Values (mm):", values)

# 2. Inspect doors on this view
payload_doors = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_DoorD7_v16.dll',
    'typeName': 'RevitScript.InspectFloorDoors',
    'methodName': 'Run',
    'args': {'viewId': active_view_id}
}
req = urllib.request.Request('http://127.0.0.1:8090/api/execute', data=json.dumps(payload_doors).encode(), headers={'Content-Type': 'application/json'})
res = urllib.request.urlopen(req)
door_data = json.loads(res.read().decode())

print(f"\n=== DOORS IN VIEW {active_view_id} ({door_data.get('count')} total) ===")
for d in door_data.get('doors', []):
    print(f"Door ID {d['id']}: Mark={d.get('mark')}, Name={d.get('symName')}, X={d.get('x')}, Y={d.get('y')}, BB_X=[{d.get('bbMinX')}, {d.get('bbMaxX')}], BB_Y=[{d.get('bbMinY')}, {d.get('bbMaxY')}], Host={d.get('hostId')}")
