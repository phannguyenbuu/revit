import os
import subprocess

dwg_path = r"D:\Dropbox\_Documents\_KIEN TRUC 2026\CAX\Công an xã Gò Công Đông 40 CBCS.dwg"
scr_path = r"D:\Dropbox\_Documents\RevitAI\inspect_cad_layers.scr"
out_txt = r"D:\Dropbox\_Documents\RevitAI\cad_layers_sample.txt"

with open(scr_path, "w", encoding="ascii") as f:
    f.write(f"""(setq f (open "{out_txt.replace('\\', '/')}" "w"))
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
cmd = [accoreconsole, "/i", dwg_path, "/s", scr_path]
proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="ignore", timeout=30)

if os.path.exists(out_txt):
    with open(out_txt, "r", encoding="utf-8") as f:
        print("Sample layers from user CAD file:")
        lines = f.readlines()
        for l in lines[:40]:
            print("  ", l.strip())
else:
    print("Could not extract layers")
