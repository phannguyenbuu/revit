import urllib.request, json, sys
sys.stdout.reconfigure(encoding='utf-8')

payload = {
    'action': 'execute_dynamic',
    'dllPath': 'D:/Dropbox/_Documents/RevitAI/bin/Release/net10.0-windows/DynamicConverter_CreateTumSlabWithHole.dll',
    'typeName': 'RevitScript.InspectAllColumnsStructure',
    'methodName': 'Run'
}
req = urllib.request.Request('http://127.0.0.1:8090/api/execute', data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json; charset=utf-8'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode('utf-8'))

cols = data['cols']
from collections import defaultdict
by_pos = defaultdict(list)
for c in cols:
    by_pos[(round(c['x']), round(c['y']))].append(c)

print(f"Total column positions: {len(by_pos)}")
duplicates = {k: v for k, v in by_pos.items() if len(v) > 1}
print(f"Positions with multiple columns: {len(duplicates)}")
for pos, col_list in duplicates.items():
    print(f"\nPosition {pos}:")
    for c in col_list:
        print(f"  Id {c['id']}: name={c['name']} base={c['baseLevel']} top={c['topLevel']} ({c['topElevM']}m)")
