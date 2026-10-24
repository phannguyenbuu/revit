import subprocess

scr = r"D:\Dropbox\_Documents\RevitAI\check_ext_test.scr"
with open(scr, "w", encoding="ascii") as f:
    f.write("ZOOM\nE\n(setq p1 (getvar \"EXTMIN\"))\n(setq p2 (getvar \"EXTMAX\"))\n(princ (strcat \"\\nEXTENTS_RESULT: (\" (rtos (car p1) 2 1) \",\" (rtos (cadr p1) 2 1) \") to (\" (rtos (car p2) 2 1) \",\" (rtos (cadr p2) 2 1) \")\\n\"))\n_QUIT\n_Y\n")

cmd = [r"C:\Program Files\Autodesk\AutoCAD 2022\accoreconsole.exe", "/i", r"D:\Dropbox\_Documents\RevitAI\DWG_Export_Individual\TEST_MERGE.dwg", "/s", scr]
proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="ignore", timeout=20)
for l in proc.stdout.splitlines():
    if "EXTENTS_RESULT:" in l:
        print(l)
