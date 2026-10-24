import sys
import subprocess
import os
import shutil

sys.stdout.reconfigure(encoding='utf-8')

def to_acad_unicode(s):
    res = []
    for char in s:
        cp = ord(char)
        if cp > 127:
            res.append(f'\\U+{cp:04X}')
        else:
            res.append(char)
    return ''.join(res)

s = '01. MẶT BẰNG TẦNG 1'
encoded = to_acad_unicode(s)
print('Original:', s)
print('Encoded:', encoded)

test_scr = f'''FILEDIA
0
CMDECHO
1
_-STYLE
UNICODE_TITLE
arial.ttf
0
1.0
0
_N
_N
_-TEXT
_S
UNICODE_TITLE
_J
_MC
0,0
800
0
{encoded}
_ZOOM
_E
_QSAVE
_QUIT
'''
scr_path = os.path.abspath('test_unicode_uplus.scr')
with open(scr_path, 'w', encoding='ascii') as f:
    f.write(test_scr)

dwg = r'D:\Dropbox\_Documents\RevitAI\DWG_Export_Individual\view_01.dwg'
test_dwg = r'D:\Dropbox\_Documents\RevitAI\DWG_Export_Individual\test_unicode_out2.dwg'
shutil.copyfile(dwg, test_dwg)

accore = r'C:\Program Files\Autodesk\AutoCAD 2022\accoreconsole.exe'
cmd = [accore, '/i', test_dwg, '/s', scr_path]
proc = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=30)
for line in proc.stdout.splitlines()[-25:]:
    print(line)
