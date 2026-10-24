import ctypes
import subprocess

user32 = ctypes.windll.user32
EnumThreadWindows = user32.EnumThreadWindows
EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

# Get all thread IDs of Revit (PID 30304)
out = subprocess.check_output('powershell -Command "(Get-Process -Id 30304).Threads.Id"', shell=True).decode()
tids = [int(x.strip()) for x in out.split() if x.strip().isdigit()]

print(f"Checking {len(tids)} threads...")
found = []
for tid in tids:
    def cb(h, l):
        length = user32.GetWindowTextLengthW(h)
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(h, buf, length + 1)
        clsbuf = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(h, clsbuf, 256)
        found.append((tid, h, clsbuf.value, buf.value))
        return True
    EnumThreadWindows(tid, EnumProc(cb), 0)

for tid, h, c, t in found:
    print(f"Thread: {tid} | HWND: {h} | Class: {c} | Title: '{t}'")
