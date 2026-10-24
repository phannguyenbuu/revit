import urllib.request
import json

data = json.dumps({"action": "export_fbx", "params": {}}).encode("utf-8")
req = urllib.request.Request("http://127.0.0.1:8096/api/action", data=data, headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req)
print(resp.read().decode("utf-8"))
