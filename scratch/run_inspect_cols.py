import urllib.request, json, sys
sys.stdout.reconfigure(encoding='utf-8')

payload = {
    "action": "execute_dynamic",
    "dllPath": r"D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_FourWalls.dll",
    "typeName": "RevitScript.InspectCurrentColumns",
    "methodName": "Run"
}

req = urllib.request.Request(
    "http://127.0.0.1:8090/api/execute",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode("utf-8"))
    print(f"Structural columns count: {res.get('structColumnsCount')}")
    print(f"Arch columns count: {res.get('archColumnsCount')}")
    for c in res.get('structColumns', []):
        print(f"  ID {c['id']}: {c['name']} (sym: {c['symName']}) at {c.get('loc')}")
    for c in res.get('archColumns', []):
        print(f"  Arch ID {c['id']}: {c['name']} (sym: {c['symName']}) at {c.get('loc')}")
