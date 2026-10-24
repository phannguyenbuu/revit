import sys, ctypes, json
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = None
for d in acad.Documents:
    if 'LONG TIÊN' in d.Name:
        doc = d
        break
if not doc:
    doc = acad.ActiveDocument

print(f"Document: {doc.Name}")

# Query text and dimensions near (-42096, -1521388) using SendCommand to dump to file
lisp = """(progn
  (setq ss (ssget "_C" '(-45000.0 -1525000.0) '(-39000.0 -1518000.0)))
  (setq f (open "D:/Dropbox/_Documents/RevitAI/scratch/s4_schedule_dump.txt" "w"))
  (if ss
    (repeat (setq i (sslength ss))
      (setq e (ssname ss (setq i (1- i))))
      (setq el (entget e))
      (setq typ (cdr (assoc 0 el)))
      (if (wcmatch typ "*TEXT")
        (progn
          (setq p (cdr (assoc 10 el)))
          (setq txt (cdr (assoc 1 el)))
          (write-line (strcat typ "|" txt "|" (rtos (car p) 2 1) "," (rtos (cadr p) 2 1)) f)
        )
      )
      (if (wcmatch typ "DIMENSION")
        (progn
          (setq dval (cdr (assoc 42 el)))
          (setq txt (cdr (assoc 1 el)))
          (write-line (strcat "DIM|" (if txt txt "") "|" (rtos dval 2 1)) f)
        )
      )
    )
  )
  (close f)
  (princ "\\nDONE_S4\\n")
)
"""
doc.SendCommand(lisp)
print("LISP command sent successfully")
