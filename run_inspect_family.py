import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

payload = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_FourWalls.dll',
    'typeName': 'RevitScript.InspectFamilyFormulas',
    'methodName': 'Run'
}

req = urllib.request.Request('http://127.0.0.1:8090/api/execute', data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
res = urllib.request.urlopen(req, timeout=10)
raw = res.read().decode('utf-8')
data = json.loads(raw)
with open(r'd:\Dropbox\_Documents\RevitAI\family_formulas.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Parameters with formulas:")
for p in data.get('parameters', []):
    if p.get('formula'):
        print(f"  {p['name']} = {p['formula']}")

print("\nType values for S1_1500x1400:")
for t in data.get('types', []):
    if 'S1' in t.get('typeName', ''):
        print(f"Type: {t.get('typeName')}")
        for k, v in t.get('values', {}).items():
            if any(w in k.lower() for w in ['cao', 'height', 'width', 'rộng']):
                print(f"  {k} = {v}")
