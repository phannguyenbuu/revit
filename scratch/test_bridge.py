import sys
import urllib.request
import json

sys.stdout.reconfigure(encoding='utf-8')
data = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_FourWalls.dll',
    'typeName': 'RevitScript.SearchAllGlassDoors',
    'methodName': 'Run'
}
req = urllib.request.Request('http://127.0.0.1:8090/api/execute', data=json.dumps(data).encode(), headers={'Content-Type': 'application/json'})
print('status:', urllib.request.urlopen(req).status)
