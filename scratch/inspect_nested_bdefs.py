import sys, ctypes, json
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument
if 'LONG TIÊN' not in doc.Name:
    for d in acad.Documents:
        if 'LONG TIÊN' in d.Name:
            doc = d
            break

blk_columns = doc.Blocks.Item('columns')

# Let's inspect unique block names referenced inside 'columns'
nested_block_names = set()
for i in range(blk_columns.Count):
    ent = blk_columns.Item(i)
    if ent.ObjectName == 'AcDbBlockReference':
        name = getattr(ent, 'EffectiveName', ent.Name)
        nested_block_names.add(name)

print("Unique nested block definitions:", nested_block_names)
for bn in nested_block_names:
    b = doc.Blocks.Item(bn)
    print(f"\nBlock '{bn}' has {b.Count} entities:")
    for j in range(b.Count):
        e = b.Item(j)
        p1, p2 = [0,0], [0,0]
        try:
            p1, p2 = e.GetBoundingBox()
        except:
            pass
        print(f"  [{j}] {e.ObjectName} lay={e.Layer} box=[{p1[0]:.2f}, {p1[1]:.2f}, {p2[0]:.2f}, {p2[1]:.2f}]")
