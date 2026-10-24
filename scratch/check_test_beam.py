import urllib.request, json, sys
sys.stdout.reconfigure(encoding='utf-8')

payload = {
    'action': 'execute_dynamic',
    'dllPath': 'D:/Dropbox/_Documents/RevitAI/bin/Release/net10.0-windows/DynamicConverter_CreateTumSlabWithHole.dll',
    'typeName': 'RevitScript.InspectTestBeamParams',
    'methodName': 'Run'
}
req = urllib.request.Request('http://127.0.0.1:8090/api/execute', data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json; charset=utf-8'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode('utf-8'))
    print(f"zMin={data['zMin']:.3f}, zMax={data['zMax']:.3f}")
    for p in data['pars']:
        if any(k in p['name'].lower() for k in ['z', 'offset', 'justif', 'elev', 'level', 'height', 'h']):
            print(f"  {p['name']}: {p['val']}")
