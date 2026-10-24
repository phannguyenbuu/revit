import sys
import urllib.request
import json

sys.stdout.reconfigure(encoding='utf-8')
data = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_FourWalls.dll',
    'typeName': 'RevitScript.InspectDoorsInRevit',
    'methodName': 'Run'
}
req = urllib.request.Request('http://127.0.0.1:8090/api/execute', data=json.dumps(data).encode(), headers={'Content-Type': 'application/json'})
res = json.loads(urllib.request.urlopen(req).read().decode())
for s in res.get('doorSymbols', []):
    fn = s['familyName'].lower()
    if 'nhom kinh' in fn or 'erowd' in fn or 'thuy luc' in fn or 'kinh' in fn or 'canh' in fn:
        print(s['id'], s['familyName'], '->', s['typeName'], f"{s['widthMm']}x{s['heightMm']}")
