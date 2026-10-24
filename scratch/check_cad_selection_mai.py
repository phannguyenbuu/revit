import sys, ctypes, json
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

pf = doc.ActiveSelectionSet

print(f"Selection count: {pf.Count}")
for i in range(pf.Count):
    ent = pf.Item(i)
    print(f"[{i}] Handle: {ent.Handle}, Type: {ent.ObjectName}, Layer: {ent.Layer}")
    if hasattr(ent, "Coordinates"):
        coords = list(ent.Coordinates)
        print(f"    Coords count: {len(coords)//2}, Area: {getattr(ent, 'Area', 0)/1e6:.3f} m2")

# Let's inspect drawing titles in ModelSpace to find what drawing 4B7DAA belongs to
ms = doc.ModelSpace
print("\n--- Searching for drawing titles and nearby texts ---")
texts = []
for i in range(ms.Count):
    ent = ms.Item(i)
    if ent.ObjectName in ['AcDbText', 'AcDbMText']:
        ins = ent.InsertionPoint
        txt = ent.TextString
        # Check if text mentions MÁI or TUM or Cao độ
        if any(w in txt.upper() for w in ["MÁI", "TUM", "MẶT BẰNG", "17.", "14."]):
            texts.append({"text": txt, "pos": [ins[0], ins[1]], "layer": ent.Layer})

print(f"Found {len(texts)} relevant title/level texts:")
for t in texts[:40]:
    print(f"  Pos: ({t['pos'][0]:.1f}, {t['pos'][1]:.1f}) [{t['layer']}]: {t['text']}")
