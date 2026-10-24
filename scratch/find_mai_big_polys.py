import sys, ctypes, time, os, json
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

res_path = "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/mai_big_polys.txt"
if os.path.exists(res_path):
    os.remove(res_path)

lsp = r'''
(defun c:FindMaiBigPolys ( / ss i ent el typ lay hnd area minpt maxpt fp)
  (setq ss (ssget "W" '(170000.0 -1415000.0) '(220000.0 -1375000.0) '((0 . "*POLYLINE"))))
  (setq fp (open "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/mai_big_polys.txt" "w"))
  (if ss
    (progn
      (setq i 0)
      (while (< i (sslength ss))
        (setq ent (ssname ss i))
        (setq el (entget ent))
        (setq lay (cdr (assoc 8 el)))
        (setq hnd (cdr (assoc 5 el)))
        (vla-getboundingbox (vlax-ename->vla-object ent) 'minpt 'maxpt)
        (setq minpt (vlax-safearray->list minpt))
        (setq maxpt (vlax-safearray->list maxpt))
        (vl-cmdf "_.area" "_O" ent)
        (setq area (getvar "AREA"))
        (write-line (strcat hnd "|" lay "|" (rtos area 2 2) "|" (rtos (car minpt) 2 1) "," (rtos (cadr minpt) 2 1) " to " (rtos (car maxpt) 2 1) "," (rtos (cadr maxpt) 2 1)) fp)
        (setq i (1+ i))
      )
    )
  )
  (close fp)
  (princ)
)
(c:FindMaiBigPolys)
'''

lsp_path = "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/find_mai_big.lsp"
with open(lsp_path, "w", encoding="utf-8") as f:
    f.write(lsp)

doc.SendCommand('(load "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/find_mai_big.lsp")\n')
time.sleep(2.0)

if os.path.exists(res_path):
    with open(res_path, "r", encoding="latin-1", errors="replace") as f:
        lines = f.readlines()
    print(f"Polylines in MẶT BẰNG TẦNG MÁI ({len(lines)} found):")
    for l in lines:
        parts = l.strip().split('|')
        if len(parts) >= 4 and float(parts[2]) > 10.0 * 1e6:
            print(f"  Handle: {parts[0]}, Layer: {parts[1]}, Area: {float(parts[2])/1e6:.2f} m2, BBox: {parts[3]}")
else:
    print("res_path not found")
