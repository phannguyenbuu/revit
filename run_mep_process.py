import urllib.request
import json
import os
import sys

dll_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin", "Release", "net10.0-windows", "DynamicConverter_DoorD7_v16.dll")
payload = {
    "action": "execute_dynamic",
    "dllPath": dll_path,
    "typeName": "RevitScript.ProcessCoolermasterMep",
    "methodName": "Run"
}

def get_base_url():
    for p_file in [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "bridge_port.txt"),
        os.path.join(os.environ.get("TEMP", ""), "revit_bridge_port.txt")
    ]:
        if os.path.exists(p_file):
            try:
                with open(p_file, "r", encoding="utf-8") as f:
                    val = f.read().strip()
                    if val.isdigit():
                        return f"http://127.0.0.1:{val}"
            except Exception:
                pass
    for p in [8090, 8088, 8092]:
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{p}/api/status")
            with urllib.request.urlopen(req, timeout=0.5) as res:
                if res.status == 200:
                    return f"http://127.0.0.1:{p}"
        except Exception:
            pass
    return "http://127.0.0.1:8090"

base_url = get_base_url()
print(f"Connecting to Revit Bridge at {base_url}...")
print(f"Sending execute request... dll={dll_path}")
req = urllib.request.Request(
    f"{base_url}/api/execute",
    data=json.dumps(payload).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req, timeout=7200) as resp:
        res_data = resp.read().decode('utf-8')
        print("Response received:")
        print(res_data[:500])
except Exception as e:
    print(f"Request exception: {e}")
