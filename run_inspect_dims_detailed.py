import sys
import urllib.request
import json
import revit_cli

sys.stdout.reconfigure(encoding='utf-8')

payload = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_DoorD7_v16.dll',
    'typeName': 'RevitScript.InspectAllDimensionsDetailed',
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
        with open(r'D:\Dropbox\_Documents\RevitAI\inspect_dims_output.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("Inspection Results Summary:")
        for v in data.get('results', []):
            print(f"View {v['viewName']} (ID: {v['viewId']}): {v['totalDims']} dims, {v['zeroDimsCount']} with zeros")
            for d in v['dims']:
                if d['hasZero']:
                    zero_indices = [s['index'] for s in d['segments'] if s['valMm'] == 0.0 or s['valStr'] == '0']
                    print(f"  Dim ID {d['id']}: {d['numSegments']} segments, zero at indices {zero_indices}, origin: {d['origin']}")
except urllib.error.HTTPError as he:
    print(f"HTTPError: {he.code}")
    print(he.read().decode('utf-8'))
except Exception as ex:
    print(f"Error calling bridge: {ex}")
