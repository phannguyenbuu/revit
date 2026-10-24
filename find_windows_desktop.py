import ctypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Attach to interactive window station
hwinsta = user32.OpenWindowStationW("WinSta0", False, 0x037F)
if hwinsta:
    user32.SetProcessWindowStation(hwinsta)
    hdesk = user32.OpenDesktopW("Default", 0, False, 0x01FF)
    if hdesk:
        user32.SetThreadDesktop(hdesk)

EnumWindows = user32.EnumWindows
EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

found = []
def cb(h, l):
    length = user32.GetWindowTextLengthW(h)
    if length > 0:
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(h, buf, length + 1)
        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(h, ctypes.byref(pid))
        found.append((pid.value, h, buf.value))
    return True

EnumWindows(EnumProc(cb), 0)
print(f"Total windows found: {len(found)}")
for pid, h, t in found:
    if pid == 30304 or any(k in t.lower() for k in ['revit', 'autodesk']):
        print(f"PID: {pid} | HWND: {h} | Title: '{t}'")
