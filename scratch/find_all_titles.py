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

res_path = "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/all_drawing_titles.txt"
if os.path.exists(res_path):
    os.remove(res_path)

# LISP to find large texts (height >= 250 or containing MAT BANG, MAT DUNG, MAT CAT, KET CAU)
lsp = r'''
(defun c:FindTitles ( / ss i ent el txt hgt lay ins fp)
  (setq ss (ssget "X" '((0 . "*TEXT"))))
  (setq fp (open "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/all_drawing_titles.txt" "w"))
  (if ss
    (progn
      (setq i 0)
      (while (< i (sslength ss))
        (setq ent (ssname ss i))
        (setq el (entget ent))
        (setq txt (cdr (assoc 1 el)))
        (setq hgt (cdr (assoc 40 el)))
        (setq lay (cdr (assoc 8 el)))
        (setq ins (cdr (assoc 10 el)))
        (if (or (>= hgt 250.0)
                (wcmatch (strcase txt) "*MA?T BA?NG*")
                (wcmatch (strcase txt) "*MA?T U?NG*")
                (wcmatch (strcase txt) "*MA?T CA?T*")
                (wcmatch (strcase txt) "*KE?T CA?U*"))
          (write-line (strcat (rtos (car ins) 2 1) "," (rtos (cadr ins) 2 1) "|" (rtos hgt 2 1) "|" lay "|" txt) fp)
        )
        (setq i (1+ i))
      )
    )
  )
  (close fp)
  (princ)
)
(c:FindTitles)
'''

lsp_path = "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/find_titles.lsp"
with open(lsp_path, "w", encoding="utf-8") as f:
    f.write(lsp)

doc.SendCommand('(load "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/find_titles.lsp")\n')
