import urllib.request
import json
import os

def main():
    payload = {
        "action": "execute_dynamic",
        "dllPath": os.path.abspath(r"bin\Release\net10.0-windows\DynamicConverter_DoorD7_v16.dll"),
        "typeName": "RevitScript.InspectMepSystems",
        "methodName": "Run",
        "args": {}
    }

    req = urllib.request.Request(
        "http://127.0.0.1:8090/api/execute",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        data = json.loads(res.read().decode("utf-8"))
        print(json.dumps(data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
