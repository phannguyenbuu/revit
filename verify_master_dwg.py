import os
import subprocess

scr = r"D:\Dropbox\_Documents\RevitAI\verify_master.scr"
with open(scr, "w", encoding="ascii") as f:
    f.write("""ZOOM
E
(setq f (open "D:/Dropbox/_Documents/RevitAI/master_info.txt" "w"))
(setq p1 (getvar "EXTMIN"))
(setq p2 (getvar "EXTMAX"))
(write-line (strcat "EXTENTS: (" (rtos (car p1) 2 1) "," (rtos (cadr p1) 2 1) ") to (" (rtos (car p2) 2 1) "," (rtos (cadr p2) 2 1) ")") f)
(setq ss (ssget "X"))
(write-line (strcat "TOTAL_ENTITIES: " (itoa (if ss (sslength ss) 0))) f)
(close f)
_.QUIT
_Y
""")

accoreconsole = r"C:\Program Files\Autodesk\AutoCAD 2022\accoreconsole.exe"
cmd = [accoreconsole, "/i", r"D:\Dropbox\_Documents\RevitAI\DWG_Export_Individual\MAT_BANG_TONG_HOP_HANG_DOC.dwg", "/s", scr]
proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="ignore", timeout=20)

info_file = r"D:\Dropbox\_Documents\RevitAI\master_info.txt"
if os.path.exists(info_file):
    with open(info_file, "r") as f:
        print(f.read())
else:
    print("Info file not created")
