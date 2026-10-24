import ctypes
from ctypes import wintypes
import time

user32 = ctypes.windll.user32

WM_COMMAND = 0x0111
WM_CLOSE = 0x0010
IDOK = 1
IDCANCEL = 2

dialogs = []

def enum_cb(hwnd, lparam):
    if user32.IsWindowVisible(hwnd):
        length = user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        title = buff.value
        
        class_buff = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, class_buff, 256)
        cls_name = class_buff.value
        
        # Check if dialog
        if cls_name == "#32770" or "revit" in title.lower() or "warning" in title.lower():
            dialogs.append((hwnd, title, cls_name))
    return True

cb = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)(enum_cb)
user32.EnumWindows(cb, 0)

print(f"Found {len(dialogs)} candidate dialogs:")
for h, t, c in dialogs:
    print(f"HWND: {h} | Title: '{t}' | Class: '{c}'")
    # Send Enter key or IDOK to dialog
    user32.SendMessageW(h, WM_COMMAND, IDOK, 0)
