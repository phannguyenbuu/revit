import urllib.request
import json
import revit_cli
import sys

sys.stdout.reconfigure(encoding='utf-8')

base_url = revit_cli.get_base_url()
payload = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_DoorD7_v16.dll',
    'typeName': 'RevitScript.FindDoorsOnAxisC',
    'methodName': 'Run',
    'args': {}
}
req = urllib.request.Request(f'{base_url}/api/execute', data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req) as r:
    data = json.loads(r.read().decode('utf-8'))
    print("MATCHED DOORS BETWEEN GRID 9 & 10 ON AXIS C (Y=7800):")
    for d in data['matchedDoors']:
        if 29650 <= d['x'] <= 33350:
            print(f"ID: {d['id']:<8} | Level: {d['level']:<22} | X: {d['x']:<6} Y: {d['y']:<5} | Family: {d['familyName']:<32} | Type: {d['typeName']} | Mark: {d['mark']}")

    print("\nAVAILABLE D7 SYMBOLS:")
    for s in data['d7Symbols']:
        print(f"ID: {s['id']} | Family: {s['familyName']} | Type: {s['name']} | Active: {s['isActive']}")
