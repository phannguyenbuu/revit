import os
import subprocess
import json

dwg_dir = r"D:\Dropbox\_Documents\RevitAI\DWG_Export_Individual"
files = [
    "01_01.MẶT BẰNG TẦNG 1.dwg",
    "02_02.MẶT BẰNG TẦNG 2.dwg",
    "03_03.MẶT BẰNG TẦNG 3.dwg",
    "04_04.MẶT BẰNG TẦNG 4.dwg",
    "05_05.MẶT BẰNG TẦNG ÁP MÁI.dwg",
    "06_06.MẶT BẰNG TẦNG TUM.dwg",
    "07_07.MẶT BẰNG MÁI.dwg"
]

accoreconsole = r"C:\Program Files\Autodesk\AutoCAD 2022\accoreconsole.exe"

results = []

for fname in files:
    dwg_path = os.path.join(dwg_dir, fname)
    if not os.path.exists(dwg_path):
        continue
        
    scr_content = """(setq p1 (getvar "EXTMIN"))
(setq p2 (getvar "EXTMAX"))
(princ (strcat "EXTENTS: (" (rtos (car p1) 2 2) "," (rtos (cadr p1) 2 2) ") to (" (rtos (car p2) 2 2) "," (rtos (cadr p2) 2 2) ")\\n"))
_QUIT
"""
    scr_path = os.path.join(dwg_dir, "get_ext.scr")
    with open(scr_path, "w", encoding="utf-8") as f:
        f.write(scr_content)
        
    cmd = [accoreconsole, "/i", dwg_path, "/s", scr_path]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="ignore")
    
    extents = None
    for line in proc.stdout.splitlines():
        if "EXTENTS:" in line:
            extents = line.strip()
            break
            
    results.append({
        "file": fname,
        "extents": extents
    })

print(json.dumps(results, indent=2, ensure_ascii=False))
