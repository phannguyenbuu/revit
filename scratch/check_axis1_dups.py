import urllib.request, json, sys
sys.stdout.reconfigure(encoding='utf-8')

payload = {
    "action": "execute_dynamic",
    "dllPath": r"D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_FourWalls.dll",
    "typeName": "RevitScript.InspectWallsInRevit",
    "methodName": "Run"
}
req = urllib.request.Request("http://127.0.0.1:8090/api/execute", data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode("utf-8"))

axis1_walls = []
for w in res.get("walls", []):
    st = w.get("start") or {}
    en = w.get("end") or {}
    x1, x2 = st.get("x", 0), en.get("x", 0)
    y1, y2 = st.get("y", 0), en.get("y", 0)
    if abs(x1 - 0.55) < 0.2 and abs(x2 - 0.55) < 0.2:
        axis1_walls.append(w)
        print(f"Wall {w['id']} [{w['wallType']}]: ({x1:.3f}, {y1:.3f}) -> ({x2:.3f}, {y2:.3f}) len={w.get('lengthM'):.3f}")

print(f"Total Axis 1 walls: {len(axis1_walls)}")
