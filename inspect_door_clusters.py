import revit_cli
import json
import urllib.request

base = revit_cli.get_base_url()
payload = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_DoorD7_v16.dll',
    'typeName': 'RevitScript.TestSimulateBandRefs',
    'methodName': 'Run'
}
req = urllib.request.Request(base + '/api/execute', data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
res = urllib.request.urlopen(req)
data = json.loads(res.read().decode())
ab = data.get('abSorted', [])
print("AB Coords around D2-1 (1750, 3150):", [x for x in ab if 1500 <= x <= 3500])
print("AB Coords around D2-2 (5950, 7350):", [x for x in ab if 5500 <= x <= 7500])
print("AB Coords around D2-3 (8750, 10150):", [x for x in ab if 8500 <= x <= 10500])
print("AB Coords around D2-4 (13150, 14550):", [x for x in ab if 13000 <= x <= 15000])
print("AB Coords around D4-1 (15550, 16550):", [x for x in ab if 15000 <= x <= 17000])
print("AB Coords around D4-2 (22650, 23650):", [x for x in ab if 22000 <= x <= 24000])
print("AB Coords around D4-3 (30050, 31050):", [x for x in ab if 29500 <= x <= 31500])
