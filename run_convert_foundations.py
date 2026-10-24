import urllib.request
import json
import time
import os

url = 'http://127.0.0.1:8088/api/execute'

dll_path = r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter.dll'

items = [
    (
        r'C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads\machine\foundation_001.dxf',
        r'C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads\machine\foundation_001.rfa'
    ),
    (
        r'C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads\machine\foundation_002.dxf',
        r'C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads\machine\foundation_002.rfa'
    )
]

for dxf, rfa in items:
    print(f"Converting {os.path.basename(dxf)} -> {os.path.basename(rfa)}...")
    data = {
        'action': 'execute_dynamic',
        'dllPath': dll_path,
        'typeName': 'RevitScript.Script',
        'methodName': 'Run',
        'dxfPath': dxf,
        'rfaPath': rfa
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as res:
            resp = json.loads(res.read().decode('utf-8'))
            print("Response:", resp)
    except Exception as e:
        print("Error:", e)
