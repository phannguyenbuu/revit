import urllib.request
import json
import sys

if sys.stdout:
    sys.stdout.reconfigure(encoding='utf-8')

# Inspect 3ds Max selected object
max_code = """
(
    local obj = selection[1]
    if obj == undefined then "NO_SELECTION"
    else (
        "Name: " + obj.name + 
        " | Class: " + ((classof obj) as string) + 
        " | Pos: " + (obj.pos as string) + 
        " | Pivot: " + (obj.pivot as string) + 
        " | Min: " + (obj.min as string) + 
        " | Max: " + (obj.max as string) +
        " | Verts: " + (try ((getNumVerts obj) as string) catch "N/A")
    )
)
"""
req = urllib.request.Request(
    "http://127.0.0.1:8096/api/execute",
    data=json.dumps({"code": max_code}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
with urllib.request.urlopen(req) as res:
    print("3ds Max:", res.read().decode('utf-8'))
