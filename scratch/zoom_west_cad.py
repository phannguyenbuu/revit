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

# Zoom to West side: X_rvt in [-1, 10], Y_rvt in [-1, 15]
# CAD coords:
p1 = [-1.0 * 1000 - DX, -1.0 * 1000 - DY]
p2 = [10.0 * 1000 - DX, 15.0 * 1000 - DY]

lisp = f"""(progn
  (vla-ZoomWindow (vlax-get-acad-object) (vlax-3d-point '({p1[0]:.1f} {p1[1]:.1f})) (vlax-3d-point '({p2[0]:.1f} {p2[1]:.1f})))
  (princ "ZOOMED")
)
"""
with open("D:/Dropbox/_Documents/RevitAI/scratch/zoom_west.lsp", "w", encoding="utf-8") as f:
    f.write(lisp)

doc.SendCommand('(load "D:/Dropbox/_Documents/RevitAI/scratch/zoom_west.lsp")\n')
print("Zoom command sent")
