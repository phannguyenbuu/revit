import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

revit_pid = 30304
windows = []

def enum_windows_callback(hwnd, lparam):
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if pid.value == revit_pid:
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            is_visible = user32.IsWindowVisible(hwnd)
            windows.append((hwnd, is_visible, buff.value))
    return True

proc = WNDENUMPROC(enum_windows_callback)
user32.EnumWindows(proc, 0)

for h, v, t in windows:
    print(f"HWND: {h} | Visible: {v} | Title: '{t}'")
