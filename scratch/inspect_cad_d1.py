import sys, ctypes
sys.stdout.reconfigure(encoding='utf-8')
u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

cad_x = -132297.0
cad_y = -1393805.9

try:
    doc.SelectionSets.Item('SS_D1').Delete()
except:
    pass
ss = doc.SelectionSets.Add('SS_D1')

p1 = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [cad_x - 1500, cad_y - 1500, 0])
p2 = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [cad_x + 1500, cad_y + 1500, 0])
ss.Select(1, p1, p2) # 1 = acSelectionSetCrossing

print(f"Selected {ss.Count} entities near D1:")
for i in range(ss.Count):
    ent = ss.Item(i)
    obj_name = ent.ObjectName
    layer = ent.Layer
    handle = ent.Handle
    print(f"[{i}] {obj_name} | Layer: {layer} | Handle: {handle}")
    if "Block" in obj_name:
        bname = ent.Name
        eff = getattr(ent, "EffectiveName", bname)
        print(f"    Block Name: {bname}, EffectiveName: {eff}, InsPt: {ent.InsertionPoint}")
    elif "Text" in obj_name:
        print(f"    Text: {ent.TextString}")
