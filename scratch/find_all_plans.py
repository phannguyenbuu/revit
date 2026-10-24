import sys, ctypes, time, os
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

res_path = "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/all_plans.txt"
if os.path.exists(res_path):
    os.remove(res_path)

lsp = r'''
(defun c:FindAllPlans ( / ss i ent el p txt lay fp)
  (setq ss (ssget "X" '((0 . "*TEXT"))))
  (setq fp (open "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/all_plans.txt" "w"))
  (if ss
    (progn
      (setq i 0)
      (while (< i (sslength ss))
        (setq ent (ssname ss i))
        (setq el (entget ent))
        (setq p (cdr (assoc 10 el)))
        (setq txt (cdr (assoc 1 el)))
        (setq lay (cdr (assoc 8 el)))
        (if (or (vl-string-search "MAT BANG" (strcase (vl-string-translate "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ" "aaaaaaaaaaaaaaaaaeeeeeeeeeeeiiiiiooooooooooooooooouuuuuuuuuuuyyyyyd" txt)))
                (vl-string-search "MAI" (strcase (vl-string-translate "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ" "aaaaaaaaaaaaaaaaaeeeeeeeeeeeiiiiiooooooooooooooooouuuuuuuuuuuyyyyyd" txt)))
                (vl-string-search "TUM" (strcase txt)))
          (write-line (strcat (rtos (car p) 2 1) "," (rtos (cadr p) 2 1) "|" lay "|" txt) fp)
        )
        (setq i (1+ i))
      )
    )
  )
  (close fp)
  (princ)
)
(c:FindAllPlans)
'''

lsp_path = "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/find_plans.lsp"
with open(lsp_path, "w", encoding="utf-8") as f:
    f.write(lsp)

doc.SendCommand('(load "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/find_plans.lsp")\n')
time.sleep(2.0)

if os.path.exists(res_path):
    with open(res_path, "r", encoding="latin-1", errors="replace") as f:
        lines = f.readlines()
    print(f"Found {len(lines)} plan/roof related texts:")
    for l in lines:
        print("  " + l.strip())
else:
    print("res_path not found")
