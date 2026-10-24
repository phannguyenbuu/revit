import subprocess
import os

scr_content = """(vl-load-com)
(setvar "CMDECHO" 1)
(command "_.WALLADD" "_Width" "200" "_Height" "2800" "_Justify" "_Left" "0,0" "5000,0" "")
(setq ent (entlast))
(princ "\nENT_TYPE=")
(princ (cdr (assoc 0 (entget ent))))
(princ "\n")
QUIT
"""
scr_path = r"d:\Dropbox\_Documents\RevitAI\scratch\test_wall_console.scr"
with open(scr_path, "w", encoding="utf-8") as f:
    f.write(scr_content)

cmd = [r"C:\Program Files\Autodesk\AutoCAD 2022\accoreconsole.exe", "/s", scr_path]
res = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=30)
print("Returncode:", res.returncode)
print("Console output:")
for line in res.stdout.splitlines()[-35:]:
    print(line)
