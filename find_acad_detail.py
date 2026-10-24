import sys
import ctypes
from ctypes import wintypes

try:
    if sys.stdout:
        sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

user32 = ctypes.windll.user32

hWinsta = user32.OpenWindowStationW("WinSta0", False, 0x037F)
if hWinsta: user32.SetProcessWindowStation(hWinsta)
hDesk = user32.OpenDesktopW("Default", 0, False, 0x01FF)
if hDesk: user32.SetThreadDesktop(hDesk)

acad_hwnds = []

def enum_cb(hwnd, extra):
    if user32.IsWindowVisible(hwnd):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == 18996:
            length = user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            cls_buff = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls_buff, 256)
            title = buff.value.strip()
            print(f"HWND: {hwnd} | Class: {cls_buff.value} | Title: '{title}'")
            acad_hwnds.append((hwnd, cls_buff.value, title))
    return True

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
