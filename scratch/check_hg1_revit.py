import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

payload = {
    "action": "execute_dynamic",
    "dllPath": r"D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_FourWalls.dll",
    "typeName": "RevitScript.InspectWallsInRevit",
    "methodName": "Run"
}

req = urllib.request.Request(
    "http://127.0.0.1:8090/api/execute",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode("utf-8"))
    walls = res.get("walls", [])
    for w in walls:
        sx = w['start']['x']
        sy = w['start']['y']
        ex = w['end']['x']
        ey = w['end']['y']
        if (36.0 <= sx <= 38.0 or 36.0 <= ex <= 38.0) and (-0.5 <= sy <= 3.5 or -0.5 <= ey <= 3.5):
            print(f"Wall {w['id']}: type={w['wallType']}, start=({sx:.3f}, {sy:.3f}), end=({ex:.3f}, {ey:.3f}), len={w['lengthM']:.3f}m")
