import sys, ctypes
sys.stdout.reconfigure(encoding='utf-8')
u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

# Let's count all entities in modelspace with bbox in Tầng 2
min_x, max_x = -72000, -32000
min_y, max_y = -1402000, -1384000

msp = doc.ModelSpace
print(f"Total entities in ModelSpace: {msp.Count}")

all_layers = {}
walls_found = []

# Scan modelspace
for i in range(msp.Count):
    ent = msp.Item(i)
    lay = ent.Layer
    try:
        p1, p2 = ent.GetBoundingBox()
        if (p1[0] <= max_x and p2[0] >= min_x and p1[1] <= max_y and p2[1] >= min_y):
            all_layers[lay] = all_layers.get(lay, 0) + 1
            if 'tuong' in lay.lower() or 'wall' in lay.lower() or lay in ('TUONG', 'Tuong-0.5', 'A-Wall', 'A_Walls'):
                walls_found.append((ent.Handle, lay, ent.ObjectName, p1, p2))
    except:
        pass

print(f"\nEntities in Tầng 2 bounding box by layer:")
for lay, c in sorted(all_layers.items(), key=lambda x: -x[1]):
    print(f"  {lay}: {c}")

print(f"\nTotal walls found on wall layers in Tầng 2 box: {len(walls_found)}")
for h, lay, obj, p1, p2 in walls_found[:20]:
    print(f"  [{lay}] {obj} handle={h} bbox=({p1[0]:.1f}, {p1[1]:.1f}) to ({p2[0]:.1f}, {p2[1]:.1f})")
