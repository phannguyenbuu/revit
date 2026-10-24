import urllib.request, json, sys
sys.stdout.reconfigure(encoding='utf-8')

payload = {
    'action': 'execute_dynamic',
    'dllPath': 'D:/Dropbox/_Documents/RevitAI/bin/Release/net10.0-windows/DynamicConverter_CreateTumSlabWithHole.dll',
    'typeName': 'RevitScript.InspectAxis11Elements',
    'methodName': 'Run'
}
req = urllib.request.Request('http://127.0.0.1:8090/api/execute', data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json; charset=utf-8'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode('utf-8'))
    print("COLS NEAR AXIS 11:")
    for c in data['cols']:
        print(f"  Id {c['id']}: ({c['x']}, {c['y']}) base={c['baseLevel']} top={c['topLevel']} ({c['topElevM']}m)")
