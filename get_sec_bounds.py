import os
import subprocess

scr = r"D:\Dropbox\_Documents\RevitAI\get_sec_bounds.scr"
out_txt = r"D:\Dropbox\_Documents\RevitAI\sec_bounds.txt"

with open(scr, "w", encoding="ascii") as f:
    f.write(f"""ZOOM
E
(setq f (open "{out_txt.replace('\\', '/')}" "w"))
(setq p1 (getvar "EXTMIN"))
(setq p2 (getvar "EXTMAX"))
(write-line (strcat (rtos (car p1) 2 2) "," (rtos (cadr p1) 2 2)) f)
(write-line (strcat (rtos (car p2) 2 2) "," (rtos (cadr p2) 2 2)) f)
(close f)
_.QUIT
_Y
""")

accoreconsole = r"C:\Program Files\Autodesk\AutoCAD 2022\accoreconsole.exe"
cmd = [accoreconsole, "/i", r"D:\Dropbox\_Documents\RevitAI\DWG_Export_Sections\section_01.dwg", "/s", scr]
subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="ignore", timeout=20)

if os.path.exists(out_txt):
    with open(out_txt, "r") as f:
        print("Bounds of section_01:")
        print(f.read())
