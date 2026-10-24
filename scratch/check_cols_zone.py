import urllib.request
import json
import sys

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
    cols = res.get("columns", [])
    print(f"Total columns: {len(cols)}")
    for c in cols:
        x = c['x']
        y = c['y']
        if x >= 30.0 and y <= 2.0:
            print(f"Col {c['id']}: type={c['typeName']}, at=({x:.3f}, {y:.3f})")
