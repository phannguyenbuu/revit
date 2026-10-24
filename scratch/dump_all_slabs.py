import sys, ctypes, time, os, json
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

res_path = "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/all_slabs.txt"
if os.path.exists(res_path):
    os.remove(res_path)

lsp = r'''
(defun c:DumpAllSlabs ( / ss i ent el typ lay hnd area bb minpt maxpt fp)
  (setq ss (ssget "X" '((0 . "*POLYLINE") (8 . "NET HAT MONG"))))
  (setq fp (open "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/all_slabs.txt" "w"))
  (if ss
    (progn
      (setq i 0)
      (while (< i (sslength ss))
        (setq ent (ssname ss i))
        (setq el (entget ent))
        (setq typ (cdr (assoc 0 el)))
        (setq lay (cdr (assoc 8 el)))
        (setq hnd (cdr (assoc 5 el)))
        (vla-getboundingbox (vlax-ename->vla-object ent) 'minpt 'maxpt)
        (setq minpt (vlax-safearray->list minpt))
        (setq maxpt (vlax-safearray->list maxpt))
        (vl-cmdf "_.area" "_O" ent)
        (setq area (getvar "AREA"))
        (write-line (strcat hnd "|" (rtos (car minpt) 2 1) "," (rtos (cadr minpt) 2 1) "|" (rtos (car maxpt) 2 1) "," (rtos (cadr maxpt) 2 1) "|" (rtos area 2 2)) fp)
        (setq i (1+ i))
      )
    )
  )
  (close fp)
  (princ)
)
(c:DumpAllSlabs)
'''

lsp_path = "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/dump_slabs.lsp"
with open(lsp_path, "w", encoding="utf-8") as f:
    f.write(lsp)

doc.SendCommand('(load "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/dump_slabs.lsp")\n')
time.sleep(2.0)

if os.path.exists(res_path):
    with open(res_path, "r", encoding="latin-1", errors="replace") as f:
        lines = f.readlines()
    print(f"Found {len(lines)} polylines on NET HAT MONG in entire DWG:")
    for l in lines:
        parts = l.strip().split('|')
        if len(parts) >= 4:
            area = float(parts[3])
            print(f"  Handle: {parts[0]}, BBox: ({parts[1]}) to ({parts[2]}), Area: {area/1e6:.2f} m2")
else:
    print("res_path not found")
