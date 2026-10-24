import ctypes

user32 = ctypes.windll.user32
EnumThreadWindows = user32.EnumThreadWindows
EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

hwnds = []
def cb(h, l):
    length = user32.GetWindowTextLengthW(h)
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(h, buf, length + 1)
    clsbuf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(h, clsbuf, 256)
    hwnds.append((h, clsbuf.value, buf.value, bool(user32.IsWindowVisible(h))))
    return True

EnumThreadWindows(31032, EnumProc(cb), 0)
for h, c, t, v in hwnds:
    if v or t:
        print(f"HWND: {h} | Class: {c} | Vis: {v} | Title: {t}")
