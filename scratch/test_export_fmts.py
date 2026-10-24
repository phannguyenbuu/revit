import urllib.request
import json

url = "http://127.0.0.1:8096/api/execute"

code = """
(
    for c in exporterPlugin.classes collect (c as string)
)
"""

req = urllib.request.Request(
    url,
    data=json.dumps({"language": "maxscript", "code": code}).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req) as res:
    data = json.loads(res.read().decode('utf-8'))
    print(data.get("result"))
