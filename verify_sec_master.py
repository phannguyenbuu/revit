import os
import subprocess

scr = r"D:\Dropbox\_Documents\RevitAI\verify_sec_master.scr"
out_txt = r"D:\Dropbox\_Documents\RevitAI\sec_master_info.txt"

with open(scr, "w", encoding="ascii") as f:
    f.write(f"""ZOOM
E
(setq f (open "{out_txt.replace('\\', '/')}" "w"))
(setq p1 (getvar "EXTMIN"))
(setq p2 (getvar "EXTMAX"))
(write-line (strcat "EXTENTS: (" (rtos (car p1) 2 1) "," (rtos (cadr p1) 2 1) ") to (" (rtos (car p2) 2 1) "," (rtos (cadr p2) 2 1) ")") f)
(setq ss (ssget "X"))
(write-line (strcat "TOTAL_ENTITIES: " (itoa (if ss (sslength ss) 0))) f)
(write-line "--- LAYER COLORS ---" f)
(setq tbl (tblnext "LAYER" T))
(while tbl
  (setq lname (cdr (assoc 2 tbl)))
  (setq lcolor (cdr (assoc 62 tbl)))
  (write-line (strcat lname " -> Color: " (itoa lcolor)) f)
  (setq tbl (tblnext "LAYER"))
)
(close f)
_.QUIT
_Y
""")

accoreconsole = r"C:\Program Files\Autodesk\AutoCAD 2022\accoreconsole.exe"
cmd = [accoreconsole, "/i", r"D:\Dropbox\_Documents\RevitAI\DWG_Export_Sections\MAT_CAT_TONG_HOP_HANG_DOC.dwg", "/s", scr]
subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="ignore", timeout=20)

if os.path.exists(out_txt):
    with open(out_txt, "r", encoding="latin1", errors="ignore") as f:
        print(f.read())
