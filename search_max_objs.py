import urllib.request
import json

max_code = """
(
    local res = #()
    for o in objects do (
        if matchPattern o.name pattern:"*112*" or matchPattern o.name pattern:"*070*" or matchPattern o.name pattern:"*CAX*" or matchPattern o.name pattern:"*obj*" then (
            append res (o.name + " | pos:" + (o.pos as string) + " | sel:" + (o.isSelected as string))
        )
    )
    res
)
"""
req = urllib.request.Request(
    "http://127.0.0.1:8096/api/execute",
    data=json.dumps({"code": max_code}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
with urllib.request.urlopen(req) as res:
    print(res.read().decode('utf-8'))
