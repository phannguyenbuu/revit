import sys
import urllib.request
import json

sys.stdout.reconfigure(encoding='utf-8')

payload = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_DoorD7_v16.dll',
    'typeName': 'RevitScript.InspectCopyTasks',
    'methodName': 'Run'
}

import revit_cli

base_url = revit_cli.get_base_url()
req = urllib.request.Request(
    f'{base_url}/api/execute',
    data=json.dumps(payload).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)

try:
    with urllib.request.urlopen(req, timeout=120) as res:
        data = json.loads(res.read().decode('utf-8'))
        print("Inspection Result:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
except Exception as ex:
    print(f"Error calling bridge: {ex}")
