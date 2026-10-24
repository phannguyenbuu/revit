import subprocess
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Write an AutoLISP file that creates style and creates text
lsp_content = '''
(defun c:AddMyTitle ()
  (vl-load-com)
  (setvar "CMDECHO" 0)
  ;; Create Arial text style
  (if (not (tblsearch "STYLE" "UNICODE_TITLE"))
    (command "-STYLE" "UNICODE_TITLE" "arial.ttf" 0 1.0 0 "_N" "_N")
  )
  ;; Make text entity
  (entmake
    (list
      (cons 0 "TEXT")
      (cons 100 "AcDbEntity")
      (cons 100 "AcDbText")
      (cons 10 (list 0.0 0.0 0.0))
      (cons 11 (list 0.0 0.0 0.0))
      (cons 40 800.0)
      (cons 1 "01. MẶT BẰNG TẦNG 1")
      (cons 7 "UNICODE_TITLE")
      (cons 72 1) ;; Center
      (cons 73 2) ;; Middle
    )
  )
  (command "_ZOOM" "_E")
  (command "_QSAVE")
  (command "_QUIT")
)
(c:AddMyTitle)
'''

with open('test_lisp_unicode.lsp', 'w', encoding='utf-8') as f:
    f.write(lsp_content)

dwg = r'D:\Dropbox\_Documents\RevitAI\DWG_Export_Individual\view_01.dwg'
test_dwg = r'D:\Dropbox\_Documents\RevitAI\DWG_Export_Individual\test_lisp_out.dwg'
import shutil
shutil.copyfile(dwg, test_dwg)

accore = r'C:\Program Files\Autodesk\AutoCAD 2022\accoreconsole.exe'
cmd = [accore, '/i', test_dwg, '/s', os.path.abspath('test_lisp_unicode.lsp')]
proc = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=20)
print('LISP test returncode:', proc.returncode)

# Check text in file
check_scr = '(prompt (strcat "\\nCHECK_TEXT: " (cdr (assoc 1 (entget (entlast)))) "\\n"))\n_QUIT\n'
with open('check.scr', 'w', encoding='utf-8') as f:
    f.write(check_scr)

cmd2 = [accore, '/i', test_dwg, '/s', os.path.abspath('check.scr')]
proc2 = subprocess.run(cmd2, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=20)
for line in proc2.stdout.splitlines():
    if 'CHECK_TEXT' in line:
        print(line)
