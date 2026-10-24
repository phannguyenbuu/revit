import sys, ctypes, time
from PIL import ImageGrab
import win32gui, win32con

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

# Find AutoCAD window
acad_hwnd = None
def enum_cb(hwnd, _):
    global acad_hwnd
    txt = win32gui.GetWindowText(hwnd)
    if "AutoCAD" in txt and win32gui.IsWindowVisible(hwnd):
        acad_hwnd = hwnd
win32gui.EnumWindows(enum_cb, None)

print(f"AutoCAD HWND: {acad_hwnd}")
if acad_hwnd:
    # Bring to foreground or just screenshot
    try:
        win32gui.SetForegroundWindow(acad_hwnd)
    except Exception:
        pass
    time.sleep(0.5)


img = ImageGrab.grab()
out_path = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\acad_screen_west.png"
img.save(out_path)
print(f"Saved screen to {out_path}")

