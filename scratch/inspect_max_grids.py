import json
import urllib.request

url = "http://127.0.0.1:8096/api/execute"

code = """
(
    local ss = stringStream ""
    try (
        for o in objects do
        (
            if (findString o.name "TRUC" != undefined) do
            (
                format "Name: % | Class: % | Min: % | Max: %\\n" o.name (classOf o as string) o.min o.max to:ss
            )
        )
    ) catch (
        format "Error: %\\n" (getCurrentException()) to:ss
    )
    ss as string
)
"""

payload = json.dumps({"language": "maxscript", "code": code}).encode('utf-8')
req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=30) as res:
    data = json.loads(res.read().decode('utf-8'))
    print(data.get("result"))
    if "error" in data:
        print("Error:", data.get("error"))
