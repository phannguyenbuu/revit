import sys, ctypes, time, os, json, re
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

ent = doc.HandleToObject("4B7DA5")
min_pt, max_pt = ent.GetBoundingBox()
print(f"4B7DA5 BBox: ({min_pt[0]:.1f}, {min_pt[1]:.1f}) to ({max_pt[0]:.1f}, {max_pt[1]:.1f})")

# Let's inspect all BlockReferences near this bbox to find sheet title
ms = doc.ModelSpace
titles = []
for i in range(ms.Count):
    try:
        obj = ms.Item(i)
        if obj.ObjectName == 'AcDbBlockReference':
            ins = obj.InsertionPoint
            if min_pt[0] - 10000 <= ins[0] <= max_pt[0] + 10000 and min_pt[1] - 15000 <= ins[1] <= max_pt[1] + 15000:
                name = obj.EffectiveName if hasattr(obj, 'EffectiveName') else obj.Name
                # check attributes
                attrs = {}
                if obj.HasAttributes:
                    for att in obj.GetAttributes():
                        attrs[att.TagString] = att.TextString
                titles.append({'block': name, 'ins': [ins[0], ins[1]], 'attrs': attrs})
    except Exception as ex:
        pass

print(f"Found {len(titles)} block references:")
for t in titles:
    print(t)
