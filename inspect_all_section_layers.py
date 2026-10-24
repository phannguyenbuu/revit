import os
import subprocess

sec_dir = r"D:\Dropbox\_Documents\RevitAI\DWG_Export_Sections"
scr = r"D:\Dropbox\_Documents\RevitAI\get_all_sec_layers.scr"
out_txt = r"D:\Dropbox\_Documents\RevitAI\all_sec_layers.txt"

files = [f for f in os.listdir(sec_dir) if f.startswith("section_") and f.endswith(".dwg")]

all_layers = set()

for f in files:
    fpath = os.path.join(sec_dir, f).replace("\\", "/")
    tmp_out = os.path.join(sec_dir, f"{f}_layers.txt").replace("\\", "/")
    with open(scr, "w", encoding="ascii") as s:
        s.write(f"""(setq f (open "{tmp_out}" "w"))
(setq tbl (tblnext "LAYER" T))
(while tbl
  (setq lname (cdr (assoc 2 tbl)))
  (write-line lname f)
  (setq tbl (tblnext "LAYER"))
)
(close f)
_.QUIT
_Y
""")
    accoreconsole = r"C:\Program Files\Autodesk\AutoCAD 2022\accoreconsole.exe"
    cmd = [accoreconsole, "/i", os.path.join(sec_dir, f), "/s", scr]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="ignore", timeout=20)
    if os.path.exists(tmp_out):
        with open(tmp_out, "r", encoding="latin1", errors="ignore") as r:
            for l in r:
                if l.strip(): all_layers.add(l.strip())

print(f"Total unique layers across all sections: {len(all_layers)}")
sorted_layers = sorted(list(all_layers))
for l in sorted_layers:
    print("  ", l)
