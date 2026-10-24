import os
import subprocess

scr = r"D:\Dropbox\_Documents\RevitAI\get_revit_layers.scr"
out_txt = r"D:\Dropbox\_Documents\RevitAI\revit_layers.txt"

with open(scr, "w", encoding="ascii") as f:
    f.write(f"""(setq f (open "{out_txt.replace(chr(92), '/')}" "w"))
(setq tbl (tblnext "LAYER" T))
(while tbl
  (setq lname (cdr (assoc 2 tbl)))
  (setq lcolor (cdr (assoc 62 tbl)))
  (write-line (strcat lname " | Color: " (itoa lcolor)) f)
  (setq tbl (tblnext "LAYER"))
)
(close f)
_.QUIT
_Y
""")

accoreconsole = r"C:\Program Files\Autodesk\AutoCAD 2022\accoreconsole.exe"
cmd = [accoreconsole, "/i", r"D:\Dropbox\_Documents\RevitAI\DWG_Export_Sections\section_01.dwg", "/s", scr]
subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="ignore", timeout=20)

if os.path.exists(out_txt):
    with open(out_txt, "r", encoding="latin1", errors="ignore") as f:
        for line in f:
            print(line.strip())
