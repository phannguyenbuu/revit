import sys, ctypes, time, os, json
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

res_file = 'C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/mai_texts.json'
if os.path.exists(res_file):
    os.remove(res_file)

lsp = r'''
(defun c:DumpMaiTexts ( / ss i ent el p txt lay res fp)
  (setq ss (ssget "C" '(110000.0 -1415000.0) '(155000.0 -1375000.0) '((0 . "*TEXT"))))
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
  (setq fp (open "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/mai_texts.json" "w"))
  (write-line res fp)
  (close fp)
  (princ)
)
(c:DumpMaiTexts)
'''

lsp_path = 'C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/get_mai_texts.lsp'
with open(lsp_path, 'w', encoding='utf-8') as f:
    f.write(lsp)

doc.SendCommand('(load "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/get_mai_texts.lsp")\n')
time.sleep(1.5)

if os.path.exists(res_file):
    with open(res_file, 'r', encoding='latin-1', errors='replace') as f:
        data = json.load(f)
    print(f"Dumped {len(data)} texts:")
    # Filter for interesting texts: titles, levels, etc.
    titles = [d for d in data if any(k in str(d[2]).upper() for k in ["MẶT BẰNG", "MÁI", "TUM", "TẦNG", "+14", "+17", "TL", "KT"])]
    for t in sorted(titles, key=lambda x: -x[1]):
        print(f"  ({t[0]:.1f}, {t[1]:.1f}) [{t[3]}]: {t[2]}")
else:
    print("res_file not created")
