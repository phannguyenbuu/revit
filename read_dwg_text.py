import subprocess
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('read_text.scr', 'w', encoding='ascii') as f:
    f.write('(prompt (strcat "\\nENTITY_TEXT: " (cdr (assoc 1 (entget (entlast)))) "\\n"))\n_QUIT\n')

accore = r'C:\Program Files\Autodesk\AutoCAD 2022\accoreconsole.exe'
cmd = [accore, '/i', r'D:\Dropbox\_Documents\RevitAI\DWG_Export_Individual\test_unicode_out2.dwg', '/s', os.path.abspath('read_text.scr')]
proc = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=20)
for line in proc.stdout.splitlines():
    if 'ENTITY_TEXT' in line:
        print(line)
