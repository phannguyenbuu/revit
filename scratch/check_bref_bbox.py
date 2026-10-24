import sys, ctypes, json
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument
blk_ref = doc.HandleToObject('497C83')

# We can also explode a copy or test bounding box of the block reference itself
print(f"BlockRef 497C83 BoundingBox:")
p1, p2 = blk_ref.GetBoundingBox()
print(f"CAD: [{p1[0]:.2f}, {p1[1]:.2f}] to [{p2[0]:.2f}, {p2[1]:.2f}]")
x1_rvt = (p1[0] + 132847.0) / 1000.0
y1_rvt = (p1[1] + 1400405.9) / 1000.0
x2_rvt = (p2[0] + 132847.0) / 1000.0
y2_rvt = (p2[1] + 1400405.9) / 1000.0
print(f"RVT: [{x1_rvt:.4f}, {y1_rvt:.4f}] to [{x2_rvt:.4f}, {y2_rvt:.4f}]")
