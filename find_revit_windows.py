import ctypes

user32 = ctypes.windll.user32
EnumWindows = user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

titles = []
def foreach_window(hwnd, lParam):
    if user32.IsWindowVisible(hwnd):
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            titles.append((pid.value, buff.value))
    return True

EnumWindows(EnumWindowsProc(foreach_window), 0)
print(f"Total visible titled windows: {len(titles)}")
for pid, t in titles:
    if any(k in t.lower() for k in ['revit', 'autodesk', 'mau', 'error', 'warning', 'dialog']):
        print(f"PID: {pid} | {t}")
