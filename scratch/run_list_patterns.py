import urllib.request, json, sys
sys.stdout.reconfigure(encoding='utf-8')

payload = {
    "action": "execute_dynamic",
    "dllPath": r"D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_FourWalls.dll",
    "typeName": "RevitScript.ListAllFillPatterns",
    "methodName": "Run"
}

req = urllib.request.Request(
    "http://127.0.0.1:8090/api/execute",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

with urllib.request.urlopen(req) as resp:
    pats = json.loads(resp.read().decode("utf-8"))
    for p in pats:
        name_lower = p['name'].lower()
        if any(k in name_lower for k in ['ansi', 'diag', 'hatch', 'brick', 'gach', 'chay', 'line']):
            print(f"{p['id']}: {p['name']} ({p.get('target')})")
