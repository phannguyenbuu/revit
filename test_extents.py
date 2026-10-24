import subprocess
import os

dwg = r"D:\Dropbox\_Documents\RevitAI\DWG_Export_Individual\01_01.MẶT BẰNG TẦNG 1.dwg"
scr = r"D:\Dropbox\_Documents\RevitAI\test_quit.scr"

with open(scr, "w", encoding="utf-8") as f:
    f.write('(setq p1 (getvar "EXTMIN"))\n')
    f.write('(setq p2 (getvar "EXTMAX"))\n')
    f.write('(princ (strcat "EXTENTS: (" (rtos (car p1) 2 2) "," (rtos (cadr p1) 2 2) ") to (" (rtos (car p2) 2 2) "," (rtos (cadr p2) 2 2) ")\\n"))\n')
    f.write('_.QUIT\n')
    f.write('_Y\n')

cmd = [r"C:\Program Files\Autodesk\AutoCAD 2022\accoreconsole.exe", "/i", dwg, "/s", scr]
proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="ignore", timeout=15)
for line in proc.stdout.splitlines():
    if "EXTENTS:" in line:
        print(line)
