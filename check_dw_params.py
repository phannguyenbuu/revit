import urllib.request
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

p = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_Sync.dll',
    'typeName': 'RevitScript.InspectAllDoorWindowParameters',
    'methodName': 'Run'
}
req = urllib.request.Request('http://127.0.0.1:8092/api/execute', data=json.dumps(p).encode('utf-8'), headers={'Content-Type': 'application/json'})
res = json.loads(urllib.request.urlopen(req, timeout=5).read().decode('utf-8'))
for item in res:
    cat = item['cat']
    fam = item['family']
    sym = item['symbol']
    print(f"=== {cat} | {fam} | {sym} ===")
    for k, v in sorted(item['parameters'].items()):
        if any(w in k.lower() for w in ['width', 'height', 'frame', 'trim', 'proj', 'inset', 'offset', 'thick', 'depth', 'rough', 'cánh', 'khung']):
            print(f"   {k}: {v}")
