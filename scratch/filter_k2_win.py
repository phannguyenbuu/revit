import subprocess
import json

proc = subprocess.run(["powershell", "-File", "call_revit.ps1", "-typeName", "RevitScript.ListAllWindowsInRevit"], capture_output=True, text=True)
data = json.loads(proc.stdout)
for w in data.get("windows", []):
    if "K2" in w.get("fam", ""):
        print(w)
