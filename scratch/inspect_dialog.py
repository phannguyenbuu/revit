import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32
try:
    hWinsta = user32.OpenWindowStationW('WinSta0', False, 0x037F)
    if hWinsta: user32.SetProcessWindowStation(hWinsta)
    hDesk = user32.OpenDesktopW('Default', 0, False, 0x01FF)
    if hDesk: user32.SetThreadDesktop(hDesk)
except: pass

dlg_hwnd = 2040062
texts = []

def enum_child(hwnd, _):
    length = user32.GetWindowTextLengthW(hwnd)
    if length > 0:
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        cls_buff = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls_buff, 256)
        texts.append((cls_buff.value, buff.value))
    return True

user32.EnumChildWindows(dlg_hwnd, ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)(enum_child), 0)
print("Dialog contents:")
for t in texts:
    print(t)
