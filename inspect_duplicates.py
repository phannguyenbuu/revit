import urllib.request
import json

# Check 3ds Max
max_url = "http://127.0.0.1:8096/api/execute"
max_code = """
(
    local objs = for o in objects where (matchPattern o.name pattern:"*0725 CAX*" or matchPattern o.name pattern:"*Mat_Tien*") collect o.name
    local sel = for o in selection collect o.name
    "3DSMAX_OBJS|" + (objs as string) + "|SEL|" + (sel as string)
)
"""
try:
    req = urllib.request.Request(
        max_url,
        data=json.dumps({"code": max_code}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as res:
        data = json.loads(res.read().decode("utf-8"))
        print("3ds Max:", data.get("result"))
except Exception as e:
    print("3ds Max error:", e)

# Check Revit via call_revit / REST
revit_url = "http://127.0.0.1:8090/api/execute"
payload = {
    "action": "execute_dynamic",
    "dllPath": r"D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_Sync.dll",
    "typeName": "RevitScript.InspectRevitSelection",
    "methodName": "Run"
}
try:
    req2 = urllib.request.Request(
        revit_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req2, timeout=10) as res2:
        data2 = json.loads(res2.read().decode("utf-8"))
        print("Revit Selection:", json.dumps(data2, indent=2))
except Exception as e:
    print("Revit error:", e)
