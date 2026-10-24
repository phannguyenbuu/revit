import os
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

dwg_dir = r"D:\Dropbox\_Documents\RevitAI\DWG_Export_Individual"
files = [f"view_{i:02d}.dwg" for i in range(1, 13)]
accoreconsole = r"C:\Program Files\Autodesk\AutoCAD 2022\accoreconsole.exe"

for fname in files:
    dwg_path = os.path.join(dwg_dir, fname)
    if not os.path.exists(dwg_path):
        continue
    scr_content = f'(setq p1 (getvar "EXTMIN"))\n(setq p2 (getvar "EXTMAX"))\n(princ (strcat "EXT: {fname} (" (rtos (car p1) 2 0) "," (rtos (cadr p1) 2 0) ") to (" (rtos (car p2) 2 0) "," (rtos (cadr p2) 2 0) ")\\n"))\n_QUIT\n'
    scr_path = os.path.join(dwg_dir, "get_ext.scr")
    with open(scr_path, "w", encoding="ascii") as f:
        f.write(scr_content)
    cmd = [accoreconsole, "/i", dwg_path, "/s", scr_path]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="ignore", timeout=15)
    for line in proc.stdout.splitlines():
        if "EXT:" in line:
            print(line.strip())
