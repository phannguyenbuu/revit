import json
import urllib.request

url = "http://127.0.0.1:8096/api/execute"

code = """
(
    local ss = stringStream ""
    local o = getNodeByName "Layer:TRUC"
    if o != undefined do
    (
        local ns = numSplines o
        format "NumSplines: %\\n" ns to:ss
        for s = 1 to ns do
        (
            local nk = numKnots o s
            local p1 = getKnotPoint o s 1
            local p2 = getKnotPoint o s nk
            format "Spline %: % -> %\\n" s p1 p2 to:ss
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
