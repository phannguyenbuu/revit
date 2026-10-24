import sys, ctypes, time, os, json, re
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

res_path = "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/near_san_mai.txt"
if os.path.exists(res_path):
    os.remove(res_path)

# Texts near (130053, -1391234) and (145570, -1398821)
lsp = r'''
(defun c:DumpNearSanMai ( / ss i ent el p txt lay fp)
  (setq ss (ssget "C" '(115000.0 -1405000.0) '(155000.0 -1385000.0) '((0 . "*TEXT"))))
  (setq fp (open "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/near_san_mai.txt" "w"))
  (if ss
    (progn
      (setq i 0)
      (while (< i (sslength ss))
        (setq ent (ssname ss i))
        (setq el (entget ent))
        (setq p (cdr (assoc 10 el)))
        (setq txt (cdr (assoc 1 el)))
        (setq lay (cdr (assoc 8 el)))
        (write-line (strcat (rtos (car p) 2 1) "," (rtos (cadr p) 2 1) "|" lay "|" txt) fp)
        (setq i (1+ i))
      )
    )
  )
  (close fp)
  (princ)
)
(c:DumpNearSanMai)
'''

lsp_path = "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/dump_near.lsp"
with open(lsp_path, "w", encoding="utf-8") as f:
    f.write(lsp)

doc.SendCommand('(load "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/dump_near.lsp")\n')
time.sleep(2.0)

if os.path.exists(res_path):
    with open(res_path, "r", encoding="latin-1", errors="replace") as f:
        lines = f.readlines()
    print(f"Texts near SÀN MÁI ({len(lines)} found):")
    for l in lines:
        print("  " + l.strip())
else:
    print("res_path not found")
