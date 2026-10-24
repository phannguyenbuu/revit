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

# Query entities in CAD near X = 37.15, Y = 13.10
# CAD coords:
cx = 37.15 * 1000 - DX
cy = 13.10 * 1000 - DY

lisp = f"""(progn
  (setq f (open "D:/Dropbox/_Documents/RevitAI/scratch/cad_col_entities.txt" "w"))
  (setq ss (ssget "C" '({cx - 1000:.1f} {cy - 1000:.1f}) '({cx + 1000:.1f} {cy + 1000:.1f})))
  (if ss
    (repeat (setq i (sslength ss))
      (setq e (ssname ss (setq i (1- i))))
      (setq ed (entget e))
      (setq typ (cdr (assoc 0 ed)))
      (setq lyr (cdr (assoc 8 ed)))
      (setq hdl (cdr (assoc 5 ed)))
      (write-line (strcat typ "|" lyr "|" hdl) f)
    )
  )
  (close f)
  (princ)
)
"""

with open("D:/Dropbox/_Documents/RevitAI/scratch/check_col.lsp", "w", encoding="utf-8") as f:
    f.write(lisp)

doc.SendCommand('(load "D:/Dropbox/_Documents/RevitAI/scratch/check_col.lsp")\n')
time.sleep(1.0)
try:
    with open("D:/Dropbox/_Documents/RevitAI/scratch/cad_col_entities.txt", "r", encoding="utf-8") as f:
        print(f.read())
except Exception as ex:
    print("Err:", ex)
