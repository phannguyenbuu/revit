import urllib.request
import json

payload = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_FourWalls.dll',
    'typeName': 'RevitScript.InspectWallsInRevit',
    'methodName': 'Run'
}
req = urllib.request.Request('http://127.0.0.1:8090/api/execute', data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
res = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))

print("Walls near (33.35, 0.0):")
for w in res.get('walls', []):
    mx = (w['start']['x'] + w['end']['x'])/2
    my = (w['start']['y'] + w['end']['y'])/2
    if abs(mx - 33.35) < 3.0 and abs(my - 0.0) < 2.0:
        print(f"ID {w['id']}: {w['wallType']} ({w['widthMm']:.0f}mm) from ({w['start']['x']:.3f}, {w['start']['y']:.3f}) to ({w['end']['x']:.3f}, {w['end']['y']:.3f}) L={w['lengthM']:.3f}")
