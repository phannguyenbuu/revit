import urllib.request, json, sys
sys.stdout.reconfigure(encoding='utf-8')

# Query active view crop / bbox
payload = {
    "action": "execute_dynamic",
    "dllPath": r"D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_FourWalls.dll",
    "typeName": "RevitScript.InspectActiveViewDetails",
    "methodName": "Run"
}
req = urllib.request.Request("http://127.0.0.1:8090/api/execute", data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode("utf-8"))

print(json.dumps(res, indent=2, ensure_ascii=False))
