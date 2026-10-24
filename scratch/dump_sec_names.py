import sys, ctypes, time, os, json, re
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

res_path = "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/sec_names.txt"
if os.path.exists(res_path):
    os.remove(res_path)

lsp = r'''
(defun c:DumpSecNames ( / ss i ent el p txt lay fp)
  (setq ss (ssget "X" '((0 . "*TEXT"))))
  (setq fp (open "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/sec_names.txt" "w"))
  (if ss
    (progn
      (setq i 0)
      (while (< i (sslength ss))
        (setq ent (ssname ss i))
        (setq el (entget ent))
        (setq p (cdr (assoc 10 el)))
        (setq txt (cdr (assoc 1 el)))
        (setq lay (cdr (assoc 8 el)))
        (if (and (>= (car p) 90000.0) (<= (car p) 120000.0) (>= (cadr p) -1445000.0) (<= (cadr p) -1425000.0))
          (write-line (strcat (rtos (car p) 2 1) "," (rtos (cadr p) 2 1) "|" lay "|" txt) fp)
        )
        (setq i (1+ i))
      )
    )
  )
  (close fp)
  (princ)
)
(c:DumpSecNames)
'''

lsp_path = "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/dump_sec_names.lsp"
with open(lsp_path, "w", encoding="utf-8") as f:
    f.write(lsp)

doc.SendCommand('(load "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/dump_sec_names.lsp")\n')
time.sleep(2.0)

if os.path.exists(res_path):
    with open(res_path, "r", encoding="latin-1", errors="replace") as f:
        lines = f.readlines()
    print(f"Section texts ({len(lines)} found):")
    for l in sorted(lines, key=lambda x: -float(x.split(',')[1].split('|')[0])):
        print("  " + l.strip())
else:
    print("res_path not found")
