import urllib.request, json, sys
sys.stdout.reconfigure(encoding='utf-8')

payload = {
    'action': 'execute_dynamic',
    'dllPath': 'D:/Dropbox/_Documents/RevitAI/bin/Release/net10.0-windows/DynamicConverter_CreateTumSlabWithHole.dll',
    'typeName': 'RevitScript.InspectAllColumnsStructure',
    'methodName': 'Run'
}
req = urllib.request.Request('http://127.0.0.1:8090/api/execute', data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json; charset=utf-8'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode('utf-8'))
    print(f"Total columns: {data['count']}")
    for c in data['cols']:
        if c['topLevel'] == 'MẶT BẰNG TẦNG TUM' or c['x'] > 30000:
            print(f"  Id {c['id']}: ({c['x']}, {c['y']}) base={c['baseLevel']} top={c['topLevel']} ({c['topElevM']}m)")
