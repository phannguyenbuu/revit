import urllib.request
import json

url = "http://127.0.0.1:8096/api/execute"
code = """
(
    local out = ""
    for o in objects do (
        local n = o.name
        if (findString n "obj003" != undefined) or (findString n "obj004" != undefined) or (findString n "obj040" != undefined) or (findString n "obj041" != undefined) or (findString n "Object005" != undefined) or (findString n "obj007" != undefined) or (findString n "0725" != undefined) do (
            out += o.name + " | min: " + (o.min as string) + " | max: " + (o.max as string) + " | pos: " + (o.pos as string) + "\n"
        )
    )
    out
)
"""

req = urllib.request.Request(url, data=json.dumps({"language":"maxscript", "code":code}).encode("utf-8"), headers={"Content-Type":"application/json"})
with urllib.request.urlopen(req) as res:
    res_data = json.loads(res.read().decode("utf-8"))
    print(res_data.get("result", res_data))
