import urllib.request
import json

url = 'http://127.0.0.1:8090/api/execute'

payload = {
    "action": "execute_dynamic",
    "dllPath": r"D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_Sync.dll",
    "typeName": "RevitScript.Sync3dsMaxToRevitFamily",
    "methodName": "Run",
    "args": {
        "dwgPath": r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\AppData\Local\Autodesk\3dsMax\2022 - 64bit\ENU\temp\Sync_3dsMax_To_Revit.dwg",
        "maxObjectName": "0725 CAX_obj005"
    }
}

req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode('utf-8'),
    headers={"Content-Type": "application/json; charset=utf-8"}
)

try:
    with urllib.request.urlopen(req, timeout=30) as res:
        data = json.loads(res.read().decode('utf-8'))
        print(json.dumps(data, indent=2))
except Exception as ex:
    print("Error:", ex)
