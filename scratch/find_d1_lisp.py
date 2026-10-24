import ctypes
u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client

pythoncom.CoInitialize()
acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

DX = 132847.0
DY = 1400405.9

# Run AutoLISP to dump all texts matching D1 or Đ1
lisp = """
(progn
  (setq f (open "D:\\\\Dropbox\\\\_Documents\\\\RevitAI\\\\scratch\\\\d1_schedule.txt" "w"))
  (setq ss (ssget "X" '((0 . "*TEXT") (1 . "*D1*,*Đ1*"))))
  (if ss
    (repeat (setq i (sslength ss))
      (setq ent (ssname ss (setq i (1- i))))
      (setq el (entget ent))
      (setq h (cdr (assoc 5 el)))
      (setq str (cdr (assoc 1 el)))
      (setq pt (cdr (assoc 10 el)))
      (setq lay (cdr (assoc 8 el)))
      (write-line (strcat h "|" str "|" (rtos (car pt) 2 2) "|" (rtos (cadr pt) 2 2) "|" lay) f)
    )
  )
  (close f)
  (princ "\nDone LISP")
)
"""
doc.SendCommand(lisp + "\n")
print("Executed LISP")
