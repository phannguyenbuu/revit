import sys, ctypes, time
from PIL import ImageGrab
import win32gui, win32con

sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

acad_hwnd = 68130

# Bring AutoCAD to TOPMOST
win32gui.ShowWindow(acad_hwnd, win32con.SW_RESTORE)
win32gui.ShowWindow(acad_hwnd, win32con.SW_MAXIMIZE)
win32gui.SetWindowPos(acad_hwnd, win32con.HWND_TOPMOST, 0, 0, 1920, 1080, win32con.SWP_SHOWWINDOW)
win32gui.SetForegroundWindow(acad_hwnd)

time.sleep(1.0)

img = ImageGrab.grab()
out_path = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\acad_topmost.png"
img.save(out_path)
print(f"Captured screen to {out_path}")

# Revert topmost
win32gui.SetWindowPos(acad_hwnd, win32con.HWND_NOTOPMOST, 0, 0, 1920, 1080, win32con.SWP_SHOWWINDOW)
