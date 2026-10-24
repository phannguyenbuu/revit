import json
import urllib.request

url = "http://127.0.0.1:8096/api/execute"

code = """
(
    local ss = stringStream ""
    format "Total objects: %\\n" objects.count to:ss
    for o in objects do
    (
        if (findString o.name "Wall" != undefined) or (findString o.name "wall" != undefined) or (findString o.name "0725" != undefined) or (findString o.name "K2" != undefined) or (findString o.name "Tuong" != undefined) or (findString o.name "tuong" != undefined) or (findString o.name "Truc" != undefined) or (findString o.name "Grid" != undefined) do
        (
            format "Obj: % | Class: % | Pos: % | Min: % | Max: %\\n" o.name (classOf o as string) o.pos o.min o.max to:ss
        )
    )
    ss as string
)
"""

payload = json.dumps({"language": "maxscript", "code": code}).encode('utf-8')
req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=30) as res:
    data = json.loads(res.read().decode('utf-8'))
    print(data.get("result"))
