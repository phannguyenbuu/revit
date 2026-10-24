import urllib.request
import json

code = r'python.ExecuteFile @"D:\Dropbox\_Documents\RevitAI\3dsmax\max_bridge.py"'
data = json.dumps({"language": "maxscript", "code": code}).encode("utf-8")
req = urllib.request.Request("http://127.0.0.1:8096/api/execute", data=data, headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req)
print(resp.read().decode("utf-8"))
