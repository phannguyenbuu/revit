import urllib.request
import json
import revit_cli

base_url = revit_cli.get_base_url()
payload = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_DoorD7_v16.dll',
    'typeName': 'RevitScript.InspectViewParams',
    'methodName': 'Run',
    'args': {}
}
req = urllib.request.Request(f'{base_url}/api/execute', data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req) as r:
    data = json.loads(r.read().decode('utf-8'))
    print('CURRENT ORG:', data.get('currentOrg'))
    for s in data.get('samples', []):
        print(f"\n--- View {s['id']}: {s['name']} | Type: {s['viewType']} | Fam: {s['familyAndType']} ---")
        for p in s['paramsList']:
            name_low = p['name'].lower()
            if any(k in name_low for k in ['type', 'discipline', 'sub', 'group', 'family', 'schedule', 'category']):
                print(f"    {p['name']}: {p['val']}")
