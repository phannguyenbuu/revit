import sys, ctypes, time
from PIL import ImageGrab
import win32gui, win32con, win32process

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

acad_hwnd = 68130

# To force foreground window in Windows:
# AttachThreadInput
cur_thread = ctypes.windll.kernel32.GetCurrentThreadId()
target_thread, _ = win32process.GetWindowThreadProcessId(acad_hwnd)
ctypes.windll.user32.AttachThreadInput(cur_thread, target_thread, True)

win32gui.ShowWindow(acad_hwnd, win32con.SW_RESTORE)
win32gui.ShowWindow(acad_hwnd, win32con.SW_SHOWMAXIMIZED)
win32gui.BringWindowToTop(acad_hwnd)
win32gui.SetForegroundWindow(acad_hwnd)

ctypes.windll.user32.AttachThreadInput(cur_thread, target_thread, False)

time.sleep(1.0)

img = ImageGrab.grab()
out_path = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\acad_screen_actual.png"
img.save(out_path)
print(f"Captured screen to {out_path}")
