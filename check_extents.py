import subprocess
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

for v in ['view_01', 'view_02', 'view_08', 'view_10']:
    dwg = rf'D:\Dropbox\_Documents\RevitAI\DWG_Export_Individual\{v}.dwg'
    if os.path.exists(dwg):
        scr = f'(prompt (strcat "\\nEXTENTS {v}: " (vl-prin1-to-string (getvar "EXTMIN")) " to " (vl-prin1-to-string (getvar "EXTMAX")) "\\n"))\n_QUIT\n'
        with open('ext.scr', 'w', encoding='ascii') as f:
            f.write(scr)
        cmd = [r'C:\Program Files\Autodesk\AutoCAD 2022\accoreconsole.exe', '/i', dwg, '/s', os.path.abspath('ext.scr')]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        for line in proc.stdout.splitlines():
            if 'EXTENTS' in line:
                print(line)
