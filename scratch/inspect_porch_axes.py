import urllib.request
import json

url = "http://127.0.0.1:8096/api/execute"
code = """
(
    local out = ""
    local col1 = getNodeByName "0725 CAX 40cbcs_obj003"
    local col2 = getNodeByName "0725 CAX 40cbcs_obj004"
    local col3 = getNodeByName "0725 CAX 40cbcs_obj040"
    local col4 = getNodeByName "0725 CAX 40cbcs_obj041"
    
    out += "Columns Y centers:\\n"
    if col1 != undefined do out += "  Col1 (obj003): Y=" + (((col1.min.y + col1.max.y)/2.0) as string) + " X=" + (((col1.min.x + col1.max.x)/2.0) as string) + "\\n"
    if col2 != undefined do out += "  Col2 (obj004): Y=" + (((col2.min.y + col2.max.y)/2.0) as string) + " X=" + (((col2.min.x + col2.max.x)/2.0) as string) + "\\n"
    if col3 != undefined do out += "  Col3 (obj040): Y=" + (((col3.min.y + col3.max.y)/2.0) as string) + " X=" + (((col3.min.x + col3.max.x)/2.0) as string) + "\\n"
    if col4 != undefined do out += "  Col4 (obj041): Y=" + (((col4.min.y + col4.max.y)/2.0) as string) + " X=" + (((col4.min.x + col4.max.x)/2.0) as string) + "\\n"
    
    local slab = getNodeByName "0725 CAX_obj003"
    if slab != undefined do (
        out += "Slab X center=" + (((slab.min.x + slab.max.x)/2.0) as string) + " Y center=" + (((slab.min.y + slab.max.y)/2.0) as string) + "\\n"
    )
    
    local step = getNodeByName "Object005"
    if step != undefined do (
        out += "Step Object005: X=" + (((step.min.x + step.max.x)/2.0) as string) + " Y=" + (((step.min.y + step.max.y)/2.0) as string) + " min=" + (step.min as string) + " max=" + (step.max as string) + "\\n"
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
