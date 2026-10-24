import sys, ctypes, json
sys.stdout.reconfigure(encoding='utf-8')
u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)
import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

# We want to search near X in [130000, 160000], Y in [-1400000, -1370000]
print(f"Scanning entities near selection...")

texts_near = []
# Use a selection set with a window or crossing polygon
try:
    # Delete temp selection set if exists
    for ss in doc.SelectionSets:
        if ss.Name == "TUM_SEARCH":
            ss.Delete()
            break
except:
    pass

ss = doc.SelectionSets.Add("TUM_SEARCH")
# Mode 1 = acSelectionSetCrossing: 1
# Center of our bbox: X=145500, Y=-1389000
# Window +/- 20000
p1 = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [120000.0, -1410000.0, 0.0])
p2 = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [170000.0, -1370000.0, 0.0])

ss.Select(1, p1, p2)
print(f"Found {ss.Count} entities near selection window.")

nearby_texts = []
for i in range(ss.Count):
    ent = ss.Item(i)
    if 'Text' in ent.ObjectName:
        try:
            ins = ent.InsertionPoint
            nearby_texts.append({
                "text": ent.TextString,
                "layer": ent.Layer,
                "pos": [round(ins[0], 1), round(ins[1], 1)]
            })
        except:
            pass

ss.Delete()

print(f"Nearby texts count: {len(nearby_texts)}")
for t in nearby_texts:
    print(f"  [{t['layer']}] '{t['text']}' @ {t['pos']}")
