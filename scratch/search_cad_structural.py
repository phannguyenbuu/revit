import sys, ctypes, os
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = None
for d in acad.Documents:
    if 'LONG TIÊN' in d.Name:
        doc = d
        break
if not doc:
    doc = acad.ActiveDocument

res_path = "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/find_struct_plans.txt"
if os.path.exists(res_path):
    os.remove(res_path)

# LISP to search for structural titles and beam texts
lsp = r'''
(defun c:FindStructPlans ( / ss i ent el txt ins lay fp)
  (setq ss (ssget "X" '((0 . "*TEXT"))))
  (setq fp (open "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/find_struct_plans.txt" "w"))
  (if ss
    (progn
      (setq i 0)
      (while (< i (sslength ss))
        (setq ent (ssname ss i))
        (setq el (entget ent))
        (setq txt (cdr (assoc 1 el)))
        (setq lay (cdr (assoc 8 el)))
        (setq ins (cdr (assoc 10 el)))
        (if (or (wcmatch (strcase txt) "*D?M*")
                (wcmatch (strcase txt) "*K?T C?U*")
                (wcmatch (strcase txt) "*MBKC*")
                (wcmatch (strcase txt) "*200X*")
                (wcmatch (strcase txt) "*250X*")
                (wcmatch (strcase txt) "*300X*")
                (wcmatch (strcase txt) "*DS*")
                (wcmatch (strcase txt) "*D1*")
                (wcmatch (strcase txt) "*D2*"))
          (write-line (strcat (rtos (car ins) 2 1) "," (rtos (cadr ins) 2 1) "|" lay "|" txt) fp)
        )
        (setq i (1+ i))
      )
    )
  )
  (close fp)
  (princ)
)
(c:FindStructPlans)
'''

lsp_path = "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/find_struct.lsp"
with open(lsp_path, "w", encoding="utf-8") as f:
    f.write(lsp)

doc.SendCommand('(load "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/find_struct.lsp")\n')
