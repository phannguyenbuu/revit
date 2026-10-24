import sys, ctypes, json
sys.stdout.reconfigure(encoding='utf-8')
u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)
import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument

DX = 132847.0
DY = 1400405.9

def get_ent_by_handle(h):
    try:
        e = doc.HandleToObject(h)
        coords = list(e.Coordinates)
        pts = [[(coords[j] + DX) / 1000.0, (coords[j+1] + DY) / 1000.0] for j in range(0, len(coords), 2)]
        return {"handle": h, "type": e.ObjectName, "layer": e.Layer, "pts": pts, "closed": e.Closed}
    except Exception as ex:
        return {"handle": h, "err": str(ex)}

h_list = ["44C7A6", "44C7A7", "44C7A8", "44C7A9", "44C7AA", "44C7AB", "44C3C9"]
res = [get_ent_by_handle(h) for h in h_list]
print(json.dumps(res, indent=2))
