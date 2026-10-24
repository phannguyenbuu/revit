import sys
import urllib.request
import json

sys.stdout.reconfigure(encoding='utf-8')

req = urllib.request.Request('http://127.0.0.1:8090/api/execute', data=json.dumps({
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_FacadeWalls.dll',
    'typeName': 'RevitScript.InspectSelectedWallAndHosted',
    'methodName': 'Run'
}).encode('utf-8'), headers={'Content-Type': 'application/json'})

with urllib.request.urlopen(req) as res:
    data = json.loads(res.read().decode('utf-8'))
    print("Levels in project:")
    print("Data:", data)
