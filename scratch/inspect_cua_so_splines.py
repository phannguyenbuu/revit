import urllib.request
import json

url = "http://127.0.0.1:8096/api/execute"
code = """
(
    local s = getNodeByName "Layer:CUA SO"
    local out = "Layer:CUA SO splines near K2:\\n"
    if s != undefined do (
        for sp = 1 to (numSplines s) do (
            local np = numKnots s sp
            local pts = for k = 1 to np collect (getKnotPoint s sp k)
            -- check if any point is near X = -19973.3 and Y between 5000 and 7000
            local near = false
            for p in pts do (
                if (abs(p.x - (-19973.3)) < 1000 and p.y > 5000 and p.y < 7000) do near = true
            )
            if near do (
                out += "Spline " + (sp as string) + " (knots=" + (np as string) + "):\\n"
                for p in pts do out += "   " + (p as string) + "\\n"
            )
        )
    )
    out
)
"""

req = urllib.request.Request(
    url,
    data=json.dumps({"language": "maxscript", "code": code}).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req) as res:
    print(res.read().decode('utf-8'))
