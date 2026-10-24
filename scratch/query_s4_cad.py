import sys, ctypes, pythoncom, win32com.client
sys.stdout.reconfigure(encoding='utf-8')
u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

lisp = """(progn
  (setq ss (ssget "_C" '(-44000.0 -1523000.0) '(-40000.0 -1520000.0) '((0 . "*TEXT"))))
  (setq f (open "D:/Dropbox/_Documents/RevitAI/scratch/s4_details.txt" "w"))
  (if ss
    (repeat (setq i (sslength ss))
      (setq e (ssname ss (setq i (1- i))))
      (setq el (entget e))
      (setq p (cdr (assoc 10 el)))
      (setq txt (cdr (assoc 1 el)))
      (write-line (strcat txt "|" (rtos (car p) 2 2) "," (rtos (cadr p) 2 2)) f)
    )
  )
  (close f)
  (princ "DONE")
)
"""
doc.SendCommand(lisp)
print("Sent command to AutoCAD")
