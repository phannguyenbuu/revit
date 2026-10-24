import sys, ctypes, time
from PIL import ImageGrab
import win32gui, win32con

sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

acad_hwnd = None
def enum_cb(hwnd, _):
    global acad_hwnd
    txt = win32gui.GetWindowText(hwnd)
    if "AutoCAD" in txt and win32gui.IsWindowVisible(hwnd):
        acad_hwnd = hwnd
win32gui.EnumWindows(enum_cb, None)

print(f"AutoCAD HWND: {acad_hwnd}")
if acad_hwnd:
    win32gui.ShowWindow(acad_hwnd, win32con.SW_MAXIMIZE)
    u32.SwitchToThisWindow(acad_hwnd, True)
    time.sleep(1.0)


img = ImageGrab.grab()
out_path = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\acad_screen_max.png"
img.save(out_path)
print(f"Saved screen to {out_path}")
