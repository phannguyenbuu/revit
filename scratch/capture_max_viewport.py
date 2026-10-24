import urllib.request
import json
import shutil
import os

url = "http://127.0.0.1:8096/api/execute"
code = """
(
    local imgPath = (getDir #temp) + "\\\\max_viewport.png"
    local dib = gw.getViewportDib()
    dib.filename = imgPath
    save dib
    imgPath
)
"""

req = urllib.request.Request(
    url,
    data=json.dumps({"language": "maxscript", "code": code}).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req) as res:
    data = json.loads(res.read().decode('utf-8'))
    max_path = data.get("result")
    print("Max saved to:", max_path)
    
artifact_dir = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697"
dest_path = os.path.join(artifact_dir, "max_viewport_selection.png")
if os.path.exists(max_path):
    shutil.copy2(max_path, dest_path)
    print("Copied to artifact:", dest_path)
