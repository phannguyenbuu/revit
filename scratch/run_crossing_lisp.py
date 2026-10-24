import sys, ctypes, time, json
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

DX = 132847.0
DY = 1400405.9

p1_cad_x = 31.5 * 1000.0 - DX
p1_cad_y = -0.8 * 1000.0 - DY
p2_cad_x = 38.0 * 1000.0 - DX
p2_cad_y = 0.8 * 1000.0 - DY

lisp_code = f"""
(vl-load-com)
(setq pt1 (list {p1_cad_x} {p1_cad_y}))
(setq pt2 (list {p2_cad_x} {p2_cad_y}))
(setq ss (ssget "_C" pt1 pt2))
(setq f (open "D:/Dropbox/_Documents/RevitAI/scratch/k1_crossing_dump.txt" "w"))
(if ss
  (progn
    (write-line (strcat "COUNT=" (itoa (sslength ss))) f)
    (setq i 0)
    (while (< i (sslength ss))
      (setq e (ssname ss i))
      (setq ed (entget e))
      (setq obj (vlax-ename->vla-object e))
      (vla-getboundingbox obj 'minp 'maxp)
      (setq pmin (vlax-safearray->list minp))
      (setq pmax (vlax-safearray->list maxp))
      (write-line (strcat (cdr (assoc 5 ed)) "|" (cdr (assoc 0 ed)) "|" (cdr (assoc 8 ed)) "|" 
                          (rtos (car pmin) 2 3) "," (rtos (cadr pmin) 2 3) "|"
                          (rtos (car pmax) 2 3) "," (rtos (cadr pmax) 2 3)) f)
      (setq i (1+ i))
    )
  )
  (write-line "COUNT=0" f)
)
(close f)
(princ)
"""

with open("D:/Dropbox/_Documents/RevitAI/scratch/crossing.lsp", "w", encoding="utf-8") as f:
    f.write(lisp_code)

doc.SendCommand('(load "D:/Dropbox/_Documents/RevitAI/scratch/crossing.lsp")\n')
time.sleep(1.0)

try:
    with open("D:/Dropbox/_Documents/RevitAI/scratch/k1_crossing_dump.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
    print(f"Read {len(lines)} lines")
    for l in lines[:30]:
        print(l.strip())
except Exception as e:
    print("Error:", e)
