import urllib.request, json, sys
sys.stdout.reconfigure(encoding='utf-8')

payload = {
    "action": "execute_dynamic",
    "dllPath": r"D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_FourWalls.dll",
    "typeName": "RevitScript.InspectCurrentColumns",
    "methodName": "Run"
}
req = urllib.request.Request("http://127.0.0.1:8090/api/execute", data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode("utf-8"))

print(f"Total struct columns: {res.get('structColumnsCount')}")
for c in res.get('structColumns', []):
    loc = c.get('loc') or {}
    x, y = loc.get('x', 999), loc.get('y', 999)
    if -0.5 <= x <= 1.5:
        print(f"Col {c['id']} [{c['symName']}]: ({x:.3f}, {y:.3f})")
