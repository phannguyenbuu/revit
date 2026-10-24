import sys, ctypes, json
sys.stdout.reconfigure(encoding='utf-8')
u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)
import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

try:
    for ss in doc.SelectionSets:
        if ss.Name == 'DUMP_114': ss.Delete(); break
except: pass

ss = doc.SelectionSets.Add('DUMP_114')
p1 = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [100000.0, -1430000.0, 0.0])
p2 = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [200000.0, -1370000.0, 0.0])
ss.Select(1, p1, p2)

counts = {}
for i in range(ss.Count):
    ent = ss.Item(i)
    k = (ent.Layer, ent.ObjectName)
    counts[k] = counts.get(k, 0) + 1

ss.Delete()

for k, v in sorted(counts.items()):
    print(f"Layer: {k[0]:20s} Type: {k[1]:20s} Count: {v}")
