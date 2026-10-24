import urllib.request
import json

url = "http://127.0.0.1:8096/api/execute"
code = """
(
    local out = ""
    local o = getNodeByName "Layer:TRUC"
    if o != undefined and (canConvertTo o SplineShape) do (
        local s = convertToSplineShape (copy o)
        local numS = numSplines s
        for i = 1 to numS do (
            local numK = numKnots s i
            if numK >= 2 do (
                local k1 = getKnotPoint s i 1
                local k2 = getKnotPoint s i numK
                -- If vertical line (same X)
                if abs(k1.x - k2.x) < 5.0 do (
                    out += "Vertical spline: X=" + (k1.x as string) + " Y=[" + (k1.y as string) + " to " + (k2.y as string) + "]\\n"
                )
                -- If horizontal line (same Y)
                if abs(k1.y - k2.y) < 5.0 do (
                    out += "Horizontal spline: Y=" + (k1.y as string) + " X=[" + (k1.x as string) + " to " + (k2.x as string) + "]\\n"
                )
            )
        )
        delete s
    )
    out
)
"""

req = urllib.request.Request(url, data=json.dumps({"language":"maxscript", "code":code}).encode("utf-8"), headers={"Content-Type":"application/json"})
with urllib.request.urlopen(req) as res:
    data = json.loads(res.read().decode("utf-8"))
    print(data.get("result", data))
