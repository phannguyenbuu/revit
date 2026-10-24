import sys, ctypes, time, os, json, re
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

res_path = "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/elev_texts.txt"
if os.path.exists(res_path):
    os.remove(res_path)

# Let's search all texts in drawings TUM and MAI: X from 110000 to 220000, Y from -1420000 to -1380000
lsp = r'''
(defun c:DumpElevTexts ( / ss i ent el p txt lay fp)
  (setq ss (ssget "X" '((0 . "*TEXT"))))
  (setq fp (open "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/elev_texts.txt" "w"))
  (if ss
    (progn
      (setq i 0)
      (while (< i (sslength ss))
        (setq ent (ssname ss i))
        (setq el (entget ent))
        (setq p (cdr (assoc 10 el)))
        (setq txt (cdr (assoc 1 el)))
        (setq lay (cdr (assoc 8 el)))
        (if (and (>= (car p) 110000.0) (<= (car p) 220000.0) (>= (cadr p) -1420000.0) (<= (cadr p) -1380000.0))
          (if (or (vl-string-search "+" txt) (vl-string-search "14." txt) (vl-string-search "17." txt) (vl-string-search "10." txt) (vl-string-search "MAI" (strcase txt)) (vl-string-search "SAN" (strcase txt)))
            (write-line (strcat (rtos (car p) 2 1) "," (rtos (cadr p) 2 1) "|" lay "|" txt) fp)
          )
        )
        (setq i (1+ i))
      )
    )
  )
  (close fp)
  (princ)
)
(c:DumpElevTexts)
'''

lsp_path = "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/dump_elev.lsp"
with open(lsp_path, "w", encoding="utf-8") as f:
    f.write(lsp)

doc.SendCommand('(load "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/dump_elev.lsp")\n')
time.sleep(2.0)

if os.path.exists(res_path):
    with open(res_path, "r", encoding="latin-1", errors="replace") as f:
        lines = f.readlines()
    print(f"Found {len(lines)} elevation/mai texts:")
    for l in lines:
        print("  " + l.strip())
else:
    print("res_path not found")
