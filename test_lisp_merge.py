import os
import subprocess

dwg1 = r"D:\Dropbox\_Documents\RevitAI\DWG_Export_Individual\01_01.MẶT BẰNG TẦNG 1.dwg"
dwg2 = r"D:\Dropbox\_Documents\RevitAI\DWG_Export_Individual\02_02.MẶT BẰNG TẦNG 2.dwg"
test_out = r"D:\Dropbox\_Documents\RevitAI\DWG_Export_Individual\TEST_MERGE.dwg"

# Copy dwg1 to test_out
import shutil
shutil.copyfile(dwg1, test_out)

scr_path = r"D:\Dropbox\_Documents\RevitAI\DWG_Export_Individual\test_insert.scr"

# Escape backslashes for LISP
dwg2_lisp = dwg2.replace("\\", "/")

lisp_script = f"""(setvar "CMDECHO" 1)
(setvar "FILEDIA" 0)
(setvar "EXPERT" 5)
(command "._-INSERT" "{dwg2_lisp}" (list 0.0 35000.0 0.0) 1.0 1.0 0.0)
(command "._ZOOM" "_E")
(command "._QSAVE")
(command "._QUIT")
"""

with open(scr_path, "w", encoding="utf-8") as f:
    f.write(lisp_script)

accoreconsole = r"C:\Program Files\Autodesk\AutoCAD 2022\accoreconsole.exe"
cmd = [accoreconsole, "/i", test_out, "/s", scr_path]

print("Running accoreconsole...")
proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="ignore", timeout=30)

print("Exit code:", proc.returncode)
print("Output tail:")
lines = [l for l in proc.stdout.splitlines() if l.strip()]
for l in lines[-15:]:
    print("  ", l)
