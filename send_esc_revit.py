import ctypes
import time

user32 = ctypes.windll.user32

# Attach to desktop
hwinsta = user32.OpenWindowStationW("WinSta0", False, 0x037F)
if hwinsta:
    user32.SetProcessWindowStation(hwinsta)
    hdesk = user32.OpenDesktopW("Default", 0, False, 0x01FF)
    if hdesk:
        user32.SetThreadDesktop(hdesk)

hwnd = 2363154
VK_ESCAPE = 0x1B
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101

# Post Escape twice to exit any active command
user32.PostMessageW(hwnd, WM_KEYDOWN, VK_ESCAPE, 0)
time.sleep(0.05)
user32.PostMessageW(hwnd, WM_KEYUP, VK_ESCAPE, 0)
time.sleep(0.1)
user32.PostMessageW(hwnd, WM_KEYDOWN, VK_ESCAPE, 0)
time.sleep(0.05)
user32.PostMessageW(hwnd, WM_KEYUP, VK_ESCAPE, 0)

print("Sent Escape key to Revit main window.")
