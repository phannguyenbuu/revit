import revit_cli
import json
import urllib.request

base = revit_cli.get_base_url()
payload = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_DoorD7_v16.dll',
    'typeName': 'RevitScript.SetDimensionFitLength800',
    'methodName': 'Run',
    'args': {}
}

req = urllib.request.Request(
    f'{base}/api/execute',
    data=json.dumps(payload).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)

try:
    with urllib.request.urlopen(req, timeout=30) as res:
        data = json.loads(res.read().decode('utf-8'))
        print("Result:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
except Exception as ex:
    print(f"Error: {ex}")
