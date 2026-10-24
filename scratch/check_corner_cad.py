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

cx = 37.15 * 1000 - DX
cy = 13.10 * 1000 - DY

lisp = f"""(progn
  (setq pt '({cx:.1f} {cy:.1f}))
  (vla-ZoomCenter (vlax-get-acad-object) (vlax-3d-point pt) 4000)
  (setq ss (ssget "C" (list (- (car pt) 2500) (- (cadr pt) 2500)) (list (+ (car pt) 2500) (+ (cadr pt) 2500)) '((0 . "*TEXT,DIMENSION"))))
  (setq f (open "D:/Dropbox/_Documents/RevitAI/scratch/corner_texts.txt" "w"))
  (if ss
    (repeat (setq i (sslength ss))
      (setq e (ssname ss (setq i (1- i))))
      (setq ed (entget e))
      (setq typ (cdr (assoc 0 ed)))
      (if (wcmatch typ "*TEXT")
        (write-line (strcat typ "|" (cdr (assoc 1 ed))) f)
      )
      (if (wcmatch typ "DIMENSION")
        (write-line (strcat "DIM|" (rtos (cdr (assoc 42 ed)) 2 0)) f)
      )
    )
  )
  (close f)
  (princ)
)
"""
with open("D:/Dropbox/_Documents/RevitAI/scratch/corner_check.lsp", "w", encoding="utf-8") as f:
    f.write(lisp)

doc.SendCommand('(load "D:/Dropbox/_Documents/RevitAI/scratch/corner_check.lsp")\n')
time.sleep(1.0)
try:
    with open('scratch/corner_texts.txt', 'r', encoding='utf-8', errors='ignore') as f:
        print(f.read())
except Exception as ex:
    print('Err:', ex)
