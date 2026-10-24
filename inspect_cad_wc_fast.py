import sys, ctypes, json
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

def to_rvt(x, y):
    return (x + 70950.0) / 1000.0, (y + 1400406.0) / 1000.0

def to_cad(rx, ry):
    return rx * 1000.0 - 70950.0, ry * 1000.0 - 1400406.0

c_min = to_cad(33.0, 7.5)
c_max = to_cad(37.2, 10.0)

# Use ssget with window to get all entities in WC area instantly!
# In AutoCAD COM, we can use doc.SelectionSets.Add("SS_WC")
try:
    doc.SelectionSets.Item("SS_WC").Delete()
except:
    pass

ss = doc.SelectionSets.Add("SS_WC")
p1 = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [c_min[0], c_min[1], 0.0])
p2 = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [c_max[0], c_max[1], 0.0])

# Filter for S5 or A-WALL or A-DOOR
# dxf 0: LINE, LWPOLYLINE, TEXT, etc.
# dxf 8: layer
import win32com.client
filterType = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_I2, [8])
filterData = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_VARIANT, ["S5,A-WALL*,A-DOOR*"])

ss.Select(1, p1, p2, filterType, filterData) # 1 = acSelectionSetWindow / Crossing (1 = Window, 0 = null, 2 = Previous, 5 = Crossing)
print(f"Selection Window found {ss.Count} entities in WC area")

wc_ents = []
for i in range(ss.Count):
    ent = ss.Item(i)
    h = ent.Handle
    t = ent.ObjectName
    lay = ent.Layer
    b1, b2 = ent.GetBoundingBox()
    rb1 = to_rvt(b1[0], b1[1])
    rb2 = to_rvt(b2[0], b2[1])
    
    info = {
        "handle": h,
        "type": t,
        "layer": lay,
        "b1": [round(rb1[0], 3), round(rb1[1], 3)],
        "b2": [round(rb2[0], 3), round(rb2[1], 3)]
    }
    if t == 'AcDbLine':
        sp = to_rvt(ent.StartPoint[0], ent.StartPoint[1])
        ep = to_rvt(ent.EndPoint[0], ent.EndPoint[1])
        info["line"] = [round(sp[0], 3), round(sp[1], 3), round(ep[0], 3), round(ep[1], 3)]
    wc_ents.append(info)

ss.Delete()

print(f"Total WC entities on S5/A-WALL/A-DOOR: {len(wc_ents)}")
for e in wc_ents:
    if e['layer'] == 'S5':
        print(f"S5: {e}")
