import sys, ctypes, json
sys.stdout.reconfigure(encoding='utf-8')
u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

DX = 70950.0
DY = 1400406.0

# Read all entities from the crossing window of Tầng 2
for ss_old in doc.SelectionSets:
    if ss_old.Name == "Tang2All":
        ss_old.Delete()
        break

ss = doc.SelectionSets.Add("Tang2All")
pt1 = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [-72000.0, -1402000.0, 0.0])
pt2 = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [-32000.0, -1384000.0, 0.0])
ss.Select(1, pt1, pt2)

print(f"Total entities in Tầng 2: {ss.Count}")

# Let's inspect hatches (hatch patterns show where walls are hatched!)
hatches = []
for i in range(ss.Count):
    ent = ss.Item(i)
    if ent.ObjectName == 'AcDbHatch':
        p1, p2 = ent.GetBoundingBox()
        hatches.append({
            'handle': ent.Handle,
            'layer': ent.Layer,
            'pattern': ent.PatternName,
            'min': [(p1[0]+DX)/1000.0, (p1[1]+DY)/1000.0],
            'max': [(p2[0]+DX)/1000.0, (p2[1]+DY)/1000.0]
        })

print(f"Total hatches: {len(hatches)}")
for h in hatches[:25]:
    w = h['max'][0] - h['min'][0]
    ht = h['max'][1] - h['min'][1]
    print(f"  Hatch lay={h['layer']} pat={h['pattern']}: X [{h['min'][0]:.2f}, {h['max'][0]:.2f}] (w={w:.2f}), Y [{h['min'][1]:.2f}, {h['max'][1]:.2f}] (h={ht:.2f})")

ss.Delete()
