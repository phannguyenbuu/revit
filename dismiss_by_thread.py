import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32
WM_CLOSE = 0x0010
WM_COMMAND = 0x0111
IDOK = 1

def enum_thread_wnds(thread_id):
    wnds = []
    def cb(hwnd, lparam):
        length = user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        cls_buff = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls_buff, 256)
        wnds.append((hwnd, buff.value, cls_buff.value))
        return True
    
    cb_func = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)(cb)
    user32.EnumThreadWindows(thread_id, cb_func, 0)
    return wnds

import psutil
revit_pid = 30304
p = psutil.Process(revit_pid)
threads = [t.id for t in p.threads()]
print(f"Threads: {threads}")

found_any = False
for tid in threads:
    wnds = enum_thread_wnds(tid)
    for h, t, c in wnds:
        print(f"TID {tid} -> HWND {h} | Class: {c} | Title: '{t}'")
        found_any = True
        # If it's a dialog
        if c == "#32770" or "warning" in t.lower() or "error" in t.lower() or "revit" in t.lower():
            print(f"Sending IDOK/WM_CLOSE to {h}...")
            user32.PostMessageW(h, WM_COMMAND, IDOK, 0)
            user32.PostMessageW(h, WM_CLOSE, 0, 0)
