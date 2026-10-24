import urllib.request
import json

code = 'str((rt.maxFileName, rt.maxFilePath))'
data = json.dumps({"language": "python", "code": code}).encode("utf-8")
req = urllib.request.Request("http://127.0.0.1:8096/api/execute", data=data, headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req)
print(resp.read().decode("utf-8"))
