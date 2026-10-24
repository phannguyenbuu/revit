import sys
import urllib.request
import json
import revit_cli

sys.stdout.reconfigure(encoding='utf-8')

payload = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_DoorD7_v16.dll',
    'typeName': 'RevitScript.ScanAllViewsDimensions',
    'methodName': 'Run'
}

base_url = revit_cli.get_base_url()
req = urllib.request.Request(
    f'{base_url}/api/execute',
    data=json.dumps(payload).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)

try:
    with urllib.request.urlopen(req, timeout=60) as res:
        data = json.loads(res.read().decode('utf-8'))
        with open('scan_all_dims.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        for v in data.get('viewReports', []):
            print(f"View: {v['viewName']} (ID: {v['viewId']}) - Total: {v['totalDims']}, Zero: {v['dimsWithZero']}, ZerosInMiddle: {v['dimsWithZerosInMiddle']}")
            for d in v['dims']:
                if d['hasZero'] or d['hasZerosInMiddle']:
                    print(f"  Dim ID {d['id']}: numSegs={d['numSegs']}, totalSpan={d['totalSpanMm']}, origin=({d['origin']['x']}, {d['origin']['y']}), dir=({d['dir']['x']}, {d['dir']['y']})")
                    print(f"    segVals: {d['segVals']}")
except urllib.error.HTTPError as he:
    print(f"HTTPError: {he.code}")
    print(he.read().decode('utf-8'))
except Exception as ex:
    print(f"Error calling bridge: {ex}")
