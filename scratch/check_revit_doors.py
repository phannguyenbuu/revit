import urllib.request, json, sys
sys.stdout.reconfigure(encoding='utf-8')

payload = {
    "action": "execute_dynamic",
    "dllPath": r"D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_FourWalls.dll",
    "typeName": "RevitScript.InspectDoorsInRevit",
    "methodName": "Run"
}
req = urllib.request.Request("http://127.0.0.1:8090/api/execute", data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode("utf-8"))

print(f"Total door symbols: {len(res.get('doorSymbols', []))}")
for ds in res.get("doorSymbols", []):
    print(f"Type {ds['id']}: Family={ds['familyName']} Type={ds['typeName']} W={ds['widthMm']} H={ds['heightMm']}")

print(f"\nTotal existing instances: {len(res.get('existingInstances', []))}")
for d in res.get("existingInstances", []):
    print(f"Door {d['id']}: {d['family']} - {d['symbol']} at ({d['x']}, {d['y']}) host={d['hostId']}")
