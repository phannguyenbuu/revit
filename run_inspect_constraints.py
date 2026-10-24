import sys
import urllib.request
import json

sys.stdout.reconfigure(encoding='utf-8')

payload = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_CreateTumSlabWithHole.dll',
    'typeName': 'RevitScript.InspectLevelConstraints',
    'methodName': 'Run'
}

req = urllib.request.Request(
    'http://127.0.0.1:8090/api/execute',
    data=json.dumps(payload).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)

try:
    with urllib.request.urlopen(req, timeout=60) as res:
        data = json.loads(res.read().decode('utf-8'))
        print("Relevant Dims:")
        for d in data.get('relevantDims', []):
            print(d)
        print("\nLvl 1 Params:")
        for p in data.get('lvl1Params', []):
            print(f"  {p['name']}: {p['val']} (readonly: {p['isReadOnly']})")
        print("\nLvl 2 Params:")
        for p in data.get('lvl2Params', []):
            print(f"  {p['name']}: {p['val']} (readonly: {p['isReadOnly']})")
except Exception as ex:
    print(f"Error calling bridge: {ex}")
