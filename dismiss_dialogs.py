import ctypes
from ctypes import wintypes
import sys
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

WINSTA_ALL = 0x00020000 | 0x037F
DESKTOP_ALL = 0x00020000 | 0x01FF

hwinsta = user32.OpenWindowStationW("WinSta0", False, WINSTA_ALL)
if hwinsta:
    user32.SetProcessWindowStation(hwinsta)

hdesk = user32.OpenDesktopW("Default", 0, False, DESKTOP_ALL)
if hdesk:
    user32.SetThreadDesktop(hdesk)

# Get Revit PID
import subprocess
try:
    out = subprocess.check_output(["powershell", "-Command", "(Get-Process Revit).Id"]).decode().strip()
    revit_pid = int(out.split()[-1])
except Exception as e:
    print("Could not find Revit PID:", e)
    sys.exit(1)

print(f"Revit PID = {revit_pid}")

WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

WM_COMMAND = 0x0111
WM_CLOSE = 0x0010
BM_CLICK = 0x00F5

found_dialogs = []

def enum_child_proc(hwnd, lparam):
    length = user32.GetWindowTextLengthW(hwnd)
    buff = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buff, length + 1)
    title = buff.value
    
    cls_buff = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, cls_buff, 256)
    cls_name = cls_buff.value

    ctrl_id = user32.GetDlgCtrlID(hwnd)
    print(f"    Child HWND={hex(hwnd)} ID={ctrl_id} Class={cls_name} Text='{title}'")

    # If button has OK, Yes, Cancel, Close
    t_lower = title.lower()
    if "ok" in t_lower or "yes" in t_lower or "cancel" in t_lower or "close" in t_lower or ctrl_id in (1, 2):
        print(f"    -> Clicking button HWND={hex(hwnd)} ('{title}')")
        user32.SendMessageW(hwnd, BM_CLICK, 0, 0)
    return True

child_callback = WNDENUMPROC(enum_child_proc)

def enum_proc(hwnd, lparam):
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if pid.value == revit_pid:
        length = user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        title = buff.value
        
        cls_buff = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls_buff, 256)
        cls_name = cls_buff.value

        if cls_name == "#32770" or "Autodesk" in title or "Revit" in title or "Save" in title or "Warning" in title:
            print(f"Found Window: HWND={hex(hwnd)} Class={cls_name} Title='{title}'")
            # Enum child controls
            user32.EnumChildWindows(hwnd, child_callback, 0)
            # Also send IDOK (1) or IDCANCEL (2)
            user32.SendMessageW(hwnd, WM_COMMAND, 1, 0)
            user32.SendMessageW(hwnd, WM_COMMAND, 2, 0)
    return True

callback = WNDENUMPROC(enum_proc)
if hdesk:
    user32.EnumDesktopWindows(hdesk, callback, 0)
else:
    user32.EnumWindows(callback, 0)
