import urllib.request
import json

url = "http://127.0.0.1:8096/api/execute"
code = """
(
    local cols = #()
    local names = #("0725 CAX 40cbcs_obj003", "0725 CAX 40cbcs_obj004", "0725 CAX 40cbcs_obj040", "0725 CAX 40cbcs_obj041")
    for n in names do (
        local o = getNodeByName n
        if o != undefined do append cols o
    )
    selectMore cols
    selection.count
)
"""

req = urllib.request.Request(url, data=json.dumps({"language":"maxscript", "code":code}).encode("utf-8"), headers={"Content-Type":"application/json"})
with urllib.request.urlopen(req) as res:
    data = json.loads(res.read().decode("utf-8"))
    print("New selection count:", data.get("result", data))
