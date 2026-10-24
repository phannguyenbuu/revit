import urllib.request
import json

url = 'http://127.0.0.1:8096/api/execute'
code = """
(
    local sel = getCurrentSelection()
    local res = #()
    for o in sel do (
        append res (
            "Name: " + o.name + 
            " | Class: " + ((classOf o) as string) + 
            " | Pos: " + ((o.pos) as string) + 
            " | Min: " + ((o.min) as string) + 
            " | Max: " + ((o.max) as string) + 
            " | Size: " + (((o.max - o.min)) as string) +
            " | NumFaces: " + (try ((polyOp.getNumFaces o) as string) catch (try ((o.numfaces) as string) catch "N/A"))
        )
    )
    res
)
"""

req = urllib.request.Request(
    url,
    data=json.dumps({"language": "maxscript", "code": code}).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
        print("Result:", json.dumps(data, indent=2))
except Exception as e:
    print("Error:", e)
