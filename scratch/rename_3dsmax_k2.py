import urllib.request
import json

url = "http://127.0.0.1:8096/api/execute"

code = """
(
    local wins = for o in selection where (findString o.name "Object008" == undefined) collect o
    for w in wins do w.name = "K2"
    for o in selection collect o.name
)
"""

req = urllib.request.Request(
    url,
    data=json.dumps({"language": "maxscript", "code": code}).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req) as res:
    print(res.read().decode('utf-8'))
