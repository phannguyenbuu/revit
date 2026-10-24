import urllib.request
import json

code = 'rt.displayTempPrompt("Test prompt from AI Copilot", 3000)'
data = json.dumps({"language": "python", "code": code}).encode("utf-8")
req = urllib.request.Request("http://127.0.0.1:8096/api/execute", data=data, headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req)
print(resp.read().decode("utf-8"))
