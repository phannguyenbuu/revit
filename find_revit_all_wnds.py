import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32
revit_pid = 30304

def get_all_windows():
    found = []
    def enum_wnd(hwnd, lparam):
        pid = wintypes.DWORD()
        tid = user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == revit_pid:
            length = user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            cls_buff = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls_buff, 256)
            found.append((hwnd, tid, user32.IsWindowVisible(hwnd), cls_buff.value, buff.value))
        return True
    
    cb = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)(enum_wnd)
    user32.EnumWindows(cb, 0)
    return found

wnds = get_all_windows()
print(f"Total Revit windows found: {len(wnds)}")
for h, tid, v, c, t in wnds:
    if v or t:
        print(f"HWND {h} | TID {tid} | Vis: {v} | Class: {c} | Title: '{t}'")
