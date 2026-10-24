import sys, ctypes, json
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument
print(f"Document: {doc.Name}")

pf = doc.PickfirstSelectionSet
print(f"Pickfirst count: {pf.Count}")

selected_entities = []
if pf.Count > 0:
    for i in range(pf.Count):
        selected_entities.append(pf.Item(i))
else:
    act = doc.ActiveSelectionSet
    print(f"ActiveSelectionSet count: {act.Count}")
    for i in range(act.Count):
        selected_entities.append(act.Item(i))

print(f"Total selected entities: {len(selected_entities)}")

if len(selected_entities) > 0:
    xs = []
    ys = []
    layers = {}
    obj_types = {}
    sample_texts = []
    for ent in selected_entities:
        try:
            p1, p2 = ent.GetBoundingBox()
            xs.extend([p1[0], p2[0]])
            ys.extend([p1[1], p2[1]])
        except:
            pass
        layers[ent.Layer] = layers.get(ent.Layer, 0) + 1
        obj_types[ent.ObjectName] = obj_types.get(ent.ObjectName, 0) + 1
        if 'Text' in ent.ObjectName:
            try:
                sample_texts.append(ent.TextString)
            except:
                pass
                
    print(f"Bounding Box: X=[{min(xs):.1f}, {max(xs):.1f}], Y=[{min(ys):.1f}, {max(ys):.1f}]")
    print(f"Layers: {layers}")
    print(f"Object Types: {obj_types}")
    print(f"Sample Texts ({len(sample_texts)}): {sample_texts[:10]}")
    
    out_file = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\current_cad_selection_tang3.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "count": len(selected_entities),
            "bbox": [min(xs), min(ys), max(xs), max(ys)],
            "layers": layers,
            "sample_texts": sample_texts
        }, f, indent=2, ensure_ascii=False)
