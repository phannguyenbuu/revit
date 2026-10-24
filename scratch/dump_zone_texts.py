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

# Query texts in boxes around the West facade and the 2 North chases
boxes = [
    ("North Chase 8.3", 7.5, 13.0, 9.0, 14.5),
    ("North Chase 29.4", 28.5, 13.0, 30.0, 14.5),
    ("NW Corner 1-C", -0.5, 12.0, 4.0, 14.5),
    ("West Wall Top", -0.5, 9.5, 1.5, 12.5),
    ("West Wall Bottom", -0.5, 1.0, 1.5, 4.0),
    ("SW Corner 1-A", -0.5, -1.0, 6.0, 1.5)
]

lisp_cmds = ["(setq f (open \"D:/Dropbox/_Documents/RevitAI/scratch/zone_texts_dump.txt\" \"w\"))"]

for name, x1, y1, x2, y2 in boxes:
    cx1 = x1 * 1000 - DX
    cy1 = y1 * 1000 - DY
    cx2 = x2 * 1000 - DX
    cy2 = y2 * 1000 - DY
    lisp_cmds.append(f"""
(write-line "=== {name} ===" f)
(setq ss (ssget "C" '({cx1:.1f} {cy1:.1f}) '({cx2:.1f} {cy2:.1f}) '((0 . "*TEXT"))))
(if ss
  (repeat (setq i (sslength ss))
    (setq e (ssname ss (setq i (1- i))))
    (setq ed (entget e))
    (setq p (cdr (assoc 10 ed)))
    (setq rx (/ (+ (car p) {DX}) 1000.0))
    (setq ry (/ (+ (cadr p) {DY}) 1000.0))
    (write-line (strcat (cdr (assoc 1 ed)) " | (" (rtos rx 2 2) ", " (rtos ry 2 2) ")") f)
  )
)
""")

lisp_cmds.append("(close f)\n(princ)")

with open("D:/Dropbox/_Documents/RevitAI/scratch/dump_texts.lsp", "w", encoding="utf-8") as f:
    f.write("\n".join(lisp_cmds))

doc.SendCommand('(load "D:/Dropbox/_Documents/RevitAI/scratch/dump_texts.lsp")\n')
time.sleep(1.0)

try:
    with open("D:/Dropbox/_Documents/RevitAI/scratch/zone_texts_dump.txt", "r", encoding="utf-8") as f:
        print(f.read())
except Exception as ex:
    print("Err:", ex)
