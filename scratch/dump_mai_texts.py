import sys, ctypes, time, os
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

res_path = "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/mai_plan_texts.txt"
if os.path.exists(res_path):
    os.remove(res_path)

lsp = r'''
(defun c:DumpMaiTexts ( / ss i ent el typ lay txt ins fp)
  (setq ss (ssget "W" '(170000.0 -1415000.0) '(220000.0 -1375000.0) '((0 . "*TEXT"))))
  (setq fp (open "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/mai_plan_texts.txt" "w"))
  (if ss
    (progn
      (setq i 0)
      (while (< i (sslength ss))
        (setq ent (ssname ss i))
        (setq el (entget ent))
        (setq typ (cdr (assoc 0 el)))
        (setq lay (cdr (assoc 8 el)))
        (setq txt (cdr (assoc 1 el)))
        (setq ins (cdr (assoc 10 el)))
        (write-line (strcat (rtos (car ins) 2 1) "|" (rtos (cadr ins) 2 1) "|" lay "|" txt) fp)
        (setq i (1+ i))
      )
    )
  )
  (close fp)
  (princ)
)
(c:DumpMaiTexts)
'''

lsp_path = "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/dump_mai_texts.lsp"
with open(lsp_path, "w", encoding="utf-8") as f:
    f.write(lsp)

doc.SendCommand('(load "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/dump_mai_texts.lsp")\n')
time.sleep(1.5)

if os.path.exists(res_path):
    with open(res_path, "r", encoding="latin-1", errors="replace") as f:
        lines = f.readlines()
    print(f"Dumped {len(lines)} texts:")
    for l in lines:
        print("  " + l.strip())
else:
    print("res_path not found")
