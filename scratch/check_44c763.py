import sys, ctypes, time
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

# Query near 44C763 (X = 4.85, Y = -0.10 in RVT)
cx = 4.85 * 1000 - DX
cy = -0.10 * 1000 - DY

lisp = f"""(progn
  (setq f (open "D:/Dropbox/_Documents/RevitAI/scratch/text_44c763.txt" "w"))
  (setq ss (ssget "C" '({cx - 1500:.1f} {cy - 1500:.1f}) '({cx + 1500:.1f} {cy + 1500:.1f})))
  (if ss
    (repeat (setq i (sslength ss))
      (setq e (ssname ss (setq i (1- i))))
      (setq ed (entget e))
      (setq typ (cdr (assoc 0 ed)))
      (setq lyr (cdr (assoc 8 ed)))
      (setq txt (if (wcmatch typ "*TEXT") (cdr (assoc 1 ed)) ""))
      (write-line (strcat typ "|" lyr "|" txt) f)
    )
  )
  (close f)
  (princ)
)
"""
with open("D:/Dropbox/_Documents/RevitAI/scratch/check_763.lsp", "w", encoding="utf-8") as f:
    f.write(lisp)
doc.SendCommand('(load "D:/Dropbox/_Documents/RevitAI/scratch/check_763.lsp")\n')
time.sleep(1.0)
try:
    with open("D:/Dropbox/_Documents/RevitAI/scratch/text_44c763.txt", "r", encoding="utf-8") as f:
        print(f.read())
except Exception as ex:
    print("Err:", ex)
