import urllib.request
import json

url = 'http://127.0.0.1:8096/api/execute'
code = """
(
    local sel = getCurrentSelection()
    local res = #()
    for obj in sel do (
        local cloneObj = copy obj
        convertToPoly cloneObj
        local xs = #()
        for v = 1 to (polyOp.getNumVerts cloneObj) do (
            local p = polyOp.getVert cloneObj v
            append xs p.x
        )
        sort xs
        local uniqueXs = #()
        local lastX = -1e9
        for x in xs do (
            if (abs (x - lastX)) > 1.0 do (
                append uniqueXs x
                lastX = x
            )
        )
        append res ("Obj: " + obj.name + " | Unique X coords: " + (uniqueXs as string))
        delete cloneObj
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
