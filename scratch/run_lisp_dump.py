import sys, ctypes, time
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

# We can evaluate lisp expressions using SendCommand or check system variables
# In AutoCAD, let's write a lisp file that dumps ssget "I" and ssget "P" to a json file!
lisp_code = """
(vl-load-com)
(setq f (open "D:/Dropbox/_Documents/RevitAI/scratch/lisp_sel_dump.txt" "w"))
(setq ssi (ssget "_I"))
(if ssi
  (progn
    (write-line (strcat "SSGET_I_COUNT=" (itoa (sslength ssi))) f)
    (setq i 0)
    (while (< i (sslength ssi))
      (setq e (ssname ssi i))
      (setq ed (entget e))
      (write-line (strcat "I," (itoa i) "," (cdr (assoc 0 ed)) "," (cdr (assoc 8 ed)) "," (cdr (assoc 5 ed))) f)
      (setq i (1+ i))
    )
  )
  (write-line "SSGET_I_COUNT=0" f)
)
(setq ssp (ssget "_P"))
(if ssp
  (progn
    (write-line (strcat "SSGET_P_COUNT=" (itoa (sslength ssp))) f)
    (setq i 0)
    (while (< i (sslength ssp))
      (setq e (ssname ssp i))
      (setq ed (entget e))
      (write-line (strcat "P," (itoa i) "," (cdr (assoc 0 ed)) "," (cdr (assoc 8 ed)) "," (cdr (assoc 5 ed))) f)
      (setq i (1+ i))
    )
  )
  (write-line "SSGET_P_COUNT=0" f)
)
(close f)
(princ)
"""

lisp_path = "D:/Dropbox/_Documents/RevitAI/scratch/dump_sel.lsp"
with open(lisp_path, "w", encoding="utf-8") as f:
    f.write(lisp_code)

doc.SendCommand(f'(load "{lisp_path}")\n')
time.sleep(1.0)

try:
    with open("D:/Dropbox/_Documents/RevitAI/scratch/lisp_sel_dump.txt", "r", encoding="utf-8") as f:
        print(f.read())
except Exception as e:
    print("Could not read dump:", e)
