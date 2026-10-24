import urllib.request, json, sys
sys.stdout.reconfigure(encoding='utf-8')

# Query Revit Grids
payload = {
    "action": "execute_dynamic",
    "dllPath": r"D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_FourWalls.dll",
    "typeName": "RevitScript.InspectGridsAndColumns",
    "methodName": "Run"
}
req = urllib.request.Request("http://127.0.0.1:8090/api/execute", data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode("utf-8"))

print("Grids:")
for g in res.get("grids", []):
    print(f"Grid {g['name']}: {g.get('curve')}")
