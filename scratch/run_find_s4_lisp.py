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

lisp = """
(vl-load-com)
(setq f (open "D:/Dropbox/_Documents/RevitAI/scratch/s4_texts.txt" "w"))
(setq ss (ssget "X" '((0 . "*TEXT") (1 . "*S4*,*s4*"))))
(if ss
  (progn
    (setq i 0)
    (while (< i (sslength ss))
      (setq e (ssname ss i))
      (setq ed (entget e))
      (setq txt (cdr (assoc 1 ed)))
      (setq ins (cdr (assoc 10 ed)))
      (write-line (strcat txt "|" (rtos (car ins) 2 2) "," (rtos (cadr ins) 2 2)) f)
      (setq i (1+ i))
    )
  )
)
(close f)
(princ)
"""

with open("D:/Dropbox/_Documents/RevitAI/scratch/find_s4.lsp", "w", encoding="utf-8") as f:
    f.write(lisp)

doc.SendCommand('(load "D:/Dropbox/_Documents/RevitAI/scratch/find_s4.lsp")\n')
time.sleep(1.0)

try:
    with open("D:/Dropbox/_Documents/RevitAI/scratch/s4_texts.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
    print(f"Found {len(lines)} texts:")
    for l in lines:
        parts = l.strip().split("|")
        t = parts[0]
        pos = [float(x) for x in parts[1].split(",")]
        x_rvt = (pos[0] + DX) / 1000.0
        y_rvt = (pos[1] + DY) / 1000.0
        print(f"  Text: '{t}', Pos RVT: ({x_rvt:.3f}, {y_rvt:.3f})")
except Exception as ex:
    print("Err:", ex)
