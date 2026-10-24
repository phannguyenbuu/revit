import urllib.request
import json

url = "http://127.0.0.1:8096/api/execute"
code = """
(
    local out = ""
    out += "Selection count: " + (selection.count as string) + "\n"
    for o in selection do (
        out += " - " + o.name + " (" + ((classOf o) as string) + ")\n"
    )
    out += "System unit: " + (units.SystemType as string) + " | scale: " + (units.SystemScale as string) + "\n"
    out += "Exporters:\n"
    for e in exporterPlugin.classes do (
        out += "   " + (e as string) + "\n"
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
    data = json.loads(res.read().decode('utf-8'))
    print(data.get("result"))
