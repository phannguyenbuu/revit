import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

payload = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_FourWalls.dll',
    'typeName': 'RevitScript.DumpWindowParams',
    'methodName': 'Run'
}

req = urllib.request.Request('http://127.0.0.1:8090/api/execute', data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
res = urllib.request.urlopen(req, timeout=10)
raw = res.read().decode('utf-8')
data = json.loads(raw)
with open(r'd:\Dropbox\_Documents\RevitAI\dump_window_params.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print('Symbol Name:', data.get('symbolName'))
print('Family Name:', data.get('familyName'))
print('\nAll Types in Family:')
for t in data.get('allTypes', []):
    print(f"  {t['name']} (id: {t['id']})")

print('\nSymbol Parameters:')
for p in data.get('symParams', []):
    if any(k in p['name'].lower() for k in ['cao', 'height', 'rộng', 'width', 'dài', 'h', 'w']):
        print(f"  {p['name']} = {p['val']} (ReadOnly: {p['isReadOnly']})")

print('\nInstance Parameters:')
for p in data.get('instParams', []):
    if any(k in p['name'].lower() for k in ['cao', 'height', 'sill', 'bậu', 'đáy', 'level', 'tầng']):
        print(f"  {p['name']} = {p['val']} (ReadOnly: {p['isReadOnly']})")
