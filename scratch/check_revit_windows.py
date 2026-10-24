import ctypes, ctypes.wintypes, subprocess

EnumWindows = ctypes.windll.user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
GetWindowText = ctypes.windll.user32.GetWindowTextW
GetClassName = ctypes.windll.user32.GetClassNameW
IsWindowVisible = ctypes.windll.user32.IsWindowVisible
GetWindowThreadProcessId = ctypes.windll.user32.GetWindowThreadProcessId

out = subprocess.check_output(['powershell', '-NoProfile', '-Command', '(Get-Process -Name Revit -ErrorAction SilentlyContinue).Id']).decode()
pids = [int(p) for p in out.split() if p.strip()]
print('Revit PIDs:', pids)

windows = []
def callback(hwnd, lparam):
    pid = ctypes.wintypes.DWORD()
    GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if pid.value in pids:
        buf_t = ctypes.create_unicode_buffer(512)
        GetWindowText(hwnd, buf_t, 512)
        buf_c = ctypes.create_unicode_buffer(512)
        GetClassName(hwnd, buf_c, 512)
        vis = IsWindowVisible(hwnd)
        if buf_t.value or buf_c.value == '#32770':
            windows.append((hwnd, pid.value, buf_c.value, buf_t.value, vis))
    return True

EnumWindows(EnumWindowsProc(callback), 0)
for w in windows:
    print(f"HWND: {w[0]}, PID: {w[1]}, Class: {w[2]}, Title: '{w[3]}'")
