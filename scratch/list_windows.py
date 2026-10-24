import sys, ctypes
import win32gui

sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

def enum_cb(hwnd, _):
    txt = win32gui.GetWindowText(hwnd)
    if txt and win32gui.IsWindowVisible(hwnd):
        print(f"HWND {hwnd}: {txt}")

win32gui.EnumWindows(enum_cb, None)
