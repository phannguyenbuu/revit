import urllib.request
import json

code = """
(
    local bMin = [1e9, 1e9, 1e9]
    local bMax = [-1e9, -1e9, -1e9]
    for o in selection do (
        bMin.x = amin bMin.x o.min.x
        bMin.y = amin bMin.y o.min.y
        bMin.z = amin bMin.z o.min.z
        
        bMax.x = amax bMax.x o.max.x
        bMax.y = amax bMax.y o.max.y
        bMax.z = amax bMax.z o.max.z
    )
    "Total BBox: Min " + (bMin as string) + " -> Max " + (bMax as string) + " | Center: " + (((bMin + bMax) / 2.0) as string)
)
"""
req = urllib.request.Request(
    "http://127.0.0.1:8096/api/execute",
    data=json.dumps({"code": code}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
with urllib.request.urlopen(req) as res:
    print(res.read().decode('utf-8'))
