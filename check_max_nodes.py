import urllib.request
import json

max_url = "http://127.0.0.1:8096/api/execute"
code = """
(
    local nodes = getNodeByName "0725 CAX_obj005" all:true
    local str = "Count: " + (nodes.count as string)
    for n in nodes do (
        str += " | " + n.name + " @ " + (n.pos as string) + " (hidden:" + (n.isHidden as string) + ")"
    )
    str
)
"""
req = urllib.request.Request(
    max_url,
    data=json.dumps({"code": code}).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req) as res:
    data = json.loads(res.read().decode("utf-8"))
    print("Result:", data.get("result"))
    if "error" in data:
        print("Error:", data["error"])
