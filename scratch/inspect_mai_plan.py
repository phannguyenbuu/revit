import sys, ctypes, time, os, json
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

res_path = "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/mai_plan_ents.txt"
if os.path.exists(res_path):
    os.remove(res_path)

# Let's zoom to MẶT BẰNG TẦNG MÁI: Center around (195000, -1395000), width 50000, height 30000
lsp = r'''
(defun c:InspectMaiPlan ( / ss i ent el typ lay hnd fp)
  (vl-cmdf "_.zoom" "_W" '(170000.0 -1415000.0) '(220000.0 -1375000.0))
  (setq ss (ssget "W" '(170000.0 -1415000.0) '(220000.0 -1375000.0)))
  (setq fp (open "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/mai_plan_ents.txt" "w"))
  (if ss
    (progn
      (setq i 0)
      (while (< i (sslength ss))
        (setq ent (ssname ss i))
        (setq el (entget ent))
        (setq typ (cdr (assoc 0 el)))
        (setq lay (cdr (assoc 8 el)))
        (setq hnd (cdr (assoc 5 el)))
        (write-line (strcat hnd "|" typ "|" lay) fp)
        (setq i (1+ i))
      )
    )
  )
  (close fp)
  (princ)
)
(c:InspectMaiPlan)
'''

lsp_path = "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/inspect_mai.lsp"
with open(lsp_path, "w", encoding="utf-8") as f:
    f.write(lsp)

doc.SendCommand('(load "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/inspect_mai.lsp")\n')
time.sleep(2.0)

if os.path.exists(res_path):
    with open(res_path, "r", encoding="latin-1", errors="replace") as f:
        lines = f.readlines()
    print(f"Found {len(lines)} entities in MẶT BẰNG TẦNG MÁI:")
    polys = [l.strip() for l in lines if "POLYLINE" in l]
    print(f"  Polylines count: {len(polys)}")
    for p in polys[:20]:
        print("    " + p)
else:
    print("res_path not found")
