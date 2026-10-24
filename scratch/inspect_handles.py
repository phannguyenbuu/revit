import sys, ctypes, json
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

# Let's inspect 4B7DA5 and 4B7DAA directly by handle!
h1 = "4B7DA5"
h2 = "4B7DAA"

for h in [h1, h2]:
    try:
        ent = doc.HandleToObject(h)
        print(f"=== Handle {h} ===")
        print(f"  Type: {ent.ObjectName}, Layer: {ent.Layer}")
        min_pt, max_pt = ent.GetBoundingBox()
        print(f"  BBox: ({min_pt[0]:.1f}, {min_pt[1]:.1f}) to ({max_pt[0]:.1f}, {max_pt[1]:.1f})")
        print(f"  Area: {ent.Area/1e6:.3f} m2")
        
        # Search nearby texts within 10m of bbox
        cx = (min_pt[0] + max_pt[0]) / 2.0
        cy = (min_pt[1] + max_pt[1]) / 2.0
        
        nearby_texts = []
        ms = doc.ModelSpace
        for i in range(ms.Count):
            obj = ms.Item(i)
            if obj.ObjectName in ['AcDbText', 'AcDbMText']:
                ins = obj.InsertionPoint
                dist = ((ins[0] - cx)**2 + (ins[1] - cy)**2)**0.5
                if dist < 25000: # within 25m
                    nearby_texts.append((dist, obj.TextString, obj.InsertionPoint, obj.Layer))
        
        print(f"  Nearby texts ({len(nearby_texts)} found):")
        for dist, txt, ins, lyr in sorted(nearby_texts, key=lambda x: x[0])[:15]:
            print(f"    d={dist/1000:.1f}m [{lyr}]: {txt}")
    except Exception as ex:
        print(f"Error inspecting {h}: {ex}")
