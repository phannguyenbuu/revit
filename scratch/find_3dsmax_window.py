import win32gui
import win32process

def callback(hwnd, results):
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    if pid == 4960:
        results.append((hwnd, pid, win32gui.GetClassName(hwnd), win32gui.GetWindowText(hwnd), win32gui.IsWindowVisible(hwnd)))
    return True

res = []
win32gui.EnumWindows(callback, res)
print(f"Windows for PID 4960: {len(res)}")
for r in res:
    print(r)
