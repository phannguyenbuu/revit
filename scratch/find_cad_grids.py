import sys, ctypes, json
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

# Search for text or grid bubbles near the slab bounding box
# X: [-140000, -90000], Y: [-1410000, -1380000]
print(f"Scanning AutoCAD entities in document: {doc.Name}...")

ms = doc.ModelSpace
grid_texts = []

for i in range(ms.Count):
    ent = ms.Item(i)
    name = ent.ObjectName
    if name in ["AcDbText", "AcDbMText"]:
        try:
            txt = ent.TextString.strip()
            ins = ent.InsertionPoint
            if -145000 <= ins[0] <= -85000 and -1415000 <= ins[1] <= -1375000:
                if txt in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "A", "B", "C", "D", "E", "TẦNG 1", "TANG 1"]:
                    grid_texts.append({
                        "text": txt,
                        "layer": ent.Layer,
                        "ins": [ins[0], ins[1], ins[2]],
                        "handle": ent.Handle
                    })
        except:
            pass

print(f"Found {len(grid_texts)} grid texts in region:")
for g in sorted(grid_texts, key=lambda x: (x['text'], x['ins'][0])):
    print(f"  {g['text']} at ({g['ins'][0]:.1f}, {g['ins'][1]:.1f}) layer={g['layer']}")
