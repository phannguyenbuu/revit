import os
import subprocess
import shutil

dwg1 = r"D:\Dropbox\_Documents\RevitAI\DWG_Export_Individual\floor_01.dwg"
dwg2 = r"D:\Dropbox\_Documents\RevitAI\DWG_Export_Individual\floor_02.dwg"
test_out = r"D:\Dropbox\_Documents\RevitAI\DWG_Export_Individual\TEST_MERGE.dwg"
shutil.copyfile(dwg1, test_out)

scr_path = r"D:\Dropbox\_Documents\RevitAI\DWG_Export_Individual\test_insert_ascii.scr"
dwg2_fwd = dwg2.replace("\\", "/")

# In pure SCR:
# -INSERT
# filename
# insertion_point (0,35000)
# scale_x (1)
# scale_y (1)
# rotation (0)
scr_content = f"""FILEDIA
0
CMDECHO
1
_-INSERT
"{dwg2_fwd}"
0,35000
1
1
0
_ZOOM
_E
_QSAVE
_QUIT
"""

with open(scr_path, "w", encoding="ascii") as f:
    f.write(scr_content)

accoreconsole = r"C:\Program Files\Autodesk\AutoCAD 2022\accoreconsole.exe"
cmd = [accoreconsole, "/i", test_out, "/s", scr_path]

proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="ignore", timeout=30)
with open(r"D:\Dropbox\_Documents\RevitAI\DWG_Export_Individual\accore_output2.txt", "w", encoding="utf-8") as out:
    out.write(proc.stdout)

print("Saved output to accore_output2.txt. Return code:", proc.returncode)
