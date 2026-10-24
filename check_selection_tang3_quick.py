import sys, ctypes, time
sys.stdout.reconfigure(encoding='utf-8')

print("1. Attaching desktop...", flush=True)
u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

print("2. CoInitialize...", flush=True)
import pythoncom, win32com.client
pythoncom.CoInitialize()

print("3. Getting AutoCAD...", flush=True)
acad = win32com.client.GetActiveObject('AutoCAD.Application')
print(f"AutoCAD version: {acad.Version}", flush=True)

doc = acad.ActiveDocument
print(f"Active Document: {doc.Name}", flush=True)

pf = doc.PickfirstSelectionSet
print(f"Pickfirst count: {pf.Count}", flush=True)

if pf.Count == 0:
    act = doc.ActiveSelectionSet
    print(f"ActiveSelectionSet count: {act.Count}", flush=True)
