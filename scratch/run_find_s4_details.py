import sys, ctypes, time
sys.stdout.reconfigure(encoding='utf-8')
u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)
import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = acad.ActiveDocument
doc.SendCommand('(load "D:/Dropbox/_Documents/RevitAI/scratch/find_s4_details.lsp")\n')
time.sleep(1.5)
try:
    with open('scratch/s4_details.txt', 'r', encoding='utf-8', errors='ignore') as f:
        print(f.read())
except Exception as ex:
    print("Err:", ex)
