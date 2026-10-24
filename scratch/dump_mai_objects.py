import sys, ctypes, time, os, json
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

res_path = "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/mai_objects.txt"
if os.path.exists(res_path):
    os.remove(res_path)

# MẶT BẰNG TẦNG MÁI is at X in [170000, 220000], Y in [-1415000, -1380000]
lsp = r'''
(defun c:DumpMaiObjects ( / ss i ent el p lay typ hnd fp area)
  (setq ss (ssget "C" '(170000.0 -1415000.0) '(220000.0 -1380000.0) '((0 . "*POLYLINE,LINE,HATCH"))))
  (setq fp (open "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/mai_objects.txt" "w"))
  (if ss
    (progn
      (setq i 0)
      (while (< i (sslength ss))
        (setq ent (ssname ss i))
        (setq el (entget ent))
        (setq typ (cdr (assoc 0 el)))
        (setq lay (cdr (assoc 8 el)))
        (setq hnd (cdr (assoc 5 el)))
        (vl-cmdf "_.area" "_O" ent)
        (setq area (getvar "AREA"))
        (write-line (strcat hnd "|" typ "|" lay "|" (rtos area 2 2)) fp)
        (setq i (1+ i))
      )
    )
  )
  (close fp)
  (princ)
)
(c:DumpMaiObjects)
'''

lsp_path = "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/dump_mai.lsp"
with open(lsp_path, "w", encoding="utf-8") as f:
    f.write(lsp)

doc.SendCommand('(load "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/dump_mai.lsp")\n')
time.sleep(2.0)

if os.path.exists(res_path):
    with open(res_path, "r", encoding="latin-1", errors="replace") as f:
        lines = f.readlines()
    print(f"Found {len(lines)} objects in MẶT BẰNG TẦNG MÁI area:")
    for l in lines:
        parts = l.strip().split('|')
        if len(parts) >= 4:
            area = float(parts[3])
            if area > 1e6: # > 1 m2
                print(f"  Handle: {parts[0]}, Type: {parts[1]}, Layer: {parts[2]}, Area: {area/1e6:.2f} m2")
else:
    print("res_path not found")
