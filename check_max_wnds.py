import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32
max_pid = 4960

def get_max_windows():
    found = []
    def enum_wnd(hwnd, lparam):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == max_pid:
            length = user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            cls_buff = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls_buff, 256)
            vis = user32.IsWindowVisible(hwnd)
            found.append((hwnd, vis, cls_buff.value, buff.value))
        return True
    
    cb = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)(enum_wnd)
    user32.EnumWindows(cb, 0)
    return found

wnds = get_max_windows()
print(f"Total 3ds Max windows found: {len(wnds)}")
for h, v, c, t in wnds:
    if v or t:
        print(f"HWND {h} | Vis: {v} | Class: {c} | Title: '{t}'")
