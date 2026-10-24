import os
import subprocess

scr = r"D:\Dropbox\_Documents\RevitAI\get_f1_bounds.scr"
with open(scr, "w", encoding="ascii") as f:
    f.write("""ZOOM
E
(setq f (open "D:/Dropbox/_Documents/RevitAI/f1_bounds.txt" "w"))
(setq p1 (getvar "EXTMIN"))
(setq p2 (getvar "EXTMAX"))
(write-line (strcat (rtos (car p1) 2 2) "," (rtos (cadr p1) 2 2)) f)
(write-line (strcat (rtos (car p2) 2 2) "," (rtos (cadr p2) 2 2)) f)
(close f)
_.QUIT
_Y
""")

accoreconsole = r"C:\Program Files\Autodesk\AutoCAD 2022\accoreconsole.exe"
cmd = [accoreconsole, "/i", r"D:\Dropbox\_Documents\RevitAI\DWG_Export_Individual\floor_01.dwg", "/s", scr]
proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="ignore", timeout=20)

bounds_file = r"D:\Dropbox\_Documents\RevitAI\f1_bounds.txt"
if os.path.exists(bounds_file):
    with open(bounds_file, "r") as f:
        print("Bounds of floor_01:")
        print(f.read())
else:
    print("Bounds file not created")
