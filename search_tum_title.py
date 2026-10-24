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
        if ss.Name == 'TITLE_SEARCH': ss.Delete(); break
except: pass

ss = doc.SelectionSets.Add('TITLE_SEARCH')
# Search within 100m of the tum
p1 = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [100000.0, -1430000.0, 0.0])
p2 = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [200000.0, -1370000.0, 0.0])
ss.Select(1, p1, p2)
print('Total entities in 100m window:', ss.Count)

texts = []
for i in range(ss.Count):
    ent = ss.Item(i)
    if 'Text' in ent.ObjectName:
        try:
            texts.append((ent.TextString, ent.Layer, ent.InsertionPoint[0], ent.InsertionPoint[1]))
        except: pass
ss.Delete()

print(f'Found {len(texts)} texts:')
for t in sorted(texts, key=lambda x: (x[3], x[2])):
    print(f'  [{t[1]:15s}] {t[0]:30s} @ ({t[2]:10.1f}, {t[3]:10.1f})')
