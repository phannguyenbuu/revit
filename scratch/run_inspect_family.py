import urllib.request, json, sys
sys.stdout.reconfigure(encoding='utf-8')

payload = {
    "action": "execute_dynamic",
    "dllPath": r"D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_FourWalls.dll",
    "typeName": "RevitScript.InspectFamilyDoc",
    "methodName": "Run"
}
req = urllib.request.Request("http://127.0.0.1:8090/api/execute", data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode("utf-8"))

print(f"Family: {res.get('familyName')}")
print("Types:", res.get("types"))
for p in res.get("parameters", []):
    print(f"  {p['name']} (isInstance={p['isInstance']}, storage={p['storage']})")
