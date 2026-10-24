import sys
import os
import ctypes
from ctypes import wintypes
import time

try:
    if sys.stdout:
        sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

user32 = ctypes.windll.user32

class COPYDATASTRUCT(ctypes.Structure):
    _fields_ = [
        ('dwData', ctypes.c_size_t),
        ('cbData', wintypes.DWORD),
        ('lpData', ctypes.c_void_p)
    ]

WM_COPYDATA = 0x004A

def get_acad_hwnd():
    try:
        hWinsta = user32.OpenWindowStationW("WinSta0", False, 0x037F)
        if hWinsta: user32.SetProcessWindowStation(hWinsta)
        hDesk = user32.OpenDesktopW("Default", 0, False, 0x01FF)
        if hDesk: user32.SetThreadDesktop(hDesk)
    except:
        pass

    acad_hwnd = None
    acad_title = ""
    def enum_cb(hwnd, extra):
        nonlocal acad_hwnd, acad_title
        if user32.IsWindowVisible(hwnd):
            cls_buff = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls_buff, 256)
            if "AfxMDIFrame" in cls_buff.value:
                length = user32.GetWindowTextLengthW(hwnd)
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                if "AutoCAD" in buff.value:
                    acad_hwnd = hwnd
                    acad_title = buff.value
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
    return acad_hwnd, acad_title

def send_acad_command(cmd_string, timeout_ms=10000, skip_esc=False):
    hwnd, title = get_acad_hwnd()
    if not hwnd:
        return False, "Không tìm thấy cửa sổ AutoCAD đang mở trên màn hình."
    
    # Gửi phím ESC để đưa AutoCAD về Command prompt sạch sẽ nếu được yêu cầu
    if not skip_esc:
        WM_KEYDOWN = 0x0100
        WM_KEYUP = 0x0101
        VK_ESCAPE = 0x1B
        for _ in range(3):
            user32.PostMessageW(hwnd, WM_KEYDOWN, VK_ESCAPE, 0)
            user32.PostMessageW(hwnd, WM_KEYUP, VK_ESCAPE, 0)
        time.sleep(0.15)

    # Ensure command ends with newline
    if not cmd_string.endswith("\n"):
        cmd_string += "\n"
        
    cmd_bytes = cmd_string.encode('utf-16le') + b'\x00\x00'
    cds = COPYDATASTRUCT()
    cds.dwData = 1
    cds.cbData = len(cmd_bytes)
    cds.lpData = ctypes.cast(ctypes.c_char_p(cmd_bytes), ctypes.c_void_p)

    SendMessageTimeout = user32.SendMessageTimeoutW
    res = wintypes.DWORD()
    ret = SendMessageTimeout(
        hwnd,
        WM_COPYDATA,
        0,
        ctypes.byref(cds),
        0x0002, # SMTO_ABORTIFHUNG
        timeout_ms,
        ctypes.byref(res)
    )
    if ret != 0:
        return True, f"Đã gửi lệnh thành công vào AutoCAD [{title}]"
    else:
        err = ctypes.GetLastError()
        return False, f"SendMessageTimeout thất bại (Error code: {err})"

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else '(princ "\\nHello from RevitAI!\\n")'
    ok, msg = send_acad_command(cmd)
    print("Success:", ok, "| Message:", msg)
