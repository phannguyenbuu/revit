import sys, ctypes, time, os, json, re
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

res_file = 'C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/drawing_titles.json'
if os.path.exists(res_file):
    os.remove(res_file)

# Search window below 4B7DA5: X from 110000 to 155000, Y from -1425000 to -1380000
lsp = r'''
(defun c:DumpTitles ( / ss i ent el p txt lay res fp)
  (setq ss (ssget "C" '(110000.0 -1425000.0) '(155000.0 -1380000.0) '((0 . "*TEXT"))))
  (setq res "[")
  (if ss
    (progn
      (setq i 0)
      (while (< i (sslength ss))
        (setq ent (ssname ss i))
        (setq el (entget ent))
        (setq p (cdr (assoc 10 el)))
        (setq txt (cdr (assoc 1 el)))
        (setq lay (cdr (assoc 8 el)))
        (if (> i 0) (setq res (strcat res ",")))
        (setq res (strcat res (vl-prin1-to-string (list (car p) (cadr p) txt lay))))
        (setq i (1+ i))
      )
    )
  )
  (setq res (strcat res "]"))
  (setq fp (open "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/drawing_titles.json" "w"))
  (write-line res fp)
  (close fp)
  (princ)
)
(c:DumpTitles)
'''

lsp_path = 'C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/get_titles.lsp'
with open(lsp_path, 'w', encoding='utf-8') as f:
    f.write(lsp)

doc.SendCommand('(load "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/get_titles.lsp")\n')
time.sleep(1.5)

if os.path.exists(res_file):
    with open(res_file, 'r', encoding='latin-1', errors='replace') as f:
        content = f.read()
    pattern = re.compile(r'\(([\d\.\+\-e]+)\s+([\d\.\+\-e]+)\s+\"([^\"]*)\"\s+\"([^\"]*)\"\)')
    matches = pattern.findall(content)
    print(f"Total texts found: {len(matches)}")
    # Find all texts with Y < -1400000 (below the plan)
    below = [m for m in matches if float(m[1]) < -1400000]
    print(f"Texts below plan (Y < -1400000):")
    for x, y, txt, lyr in sorted(below, key=lambda m: float(m[1])):
        print(f"  ({float(x):.1f}, {float(y):.1f}) [{lyr}]: {txt}")
