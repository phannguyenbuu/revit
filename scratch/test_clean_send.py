import sys
import os
import ctypes
from ctypes import wintypes
import time

user32 = ctypes.windll.user32

class COPYDATASTRUCT(ctypes.Structure):
    _fields_ = [
        ('dwData', ctypes.c_size_t),
        ('cbData', wintypes.DWORD),
        ('lpData', ctypes.c_void_p)
    ]

WM_COPYDATA = 0x004A

def get_acad_hwnd():
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

def send_clean(cmd_string):
    hwnd, title = get_acad_hwnd()
    if not hwnd:
        return False, "AutoCAD not found"

    if not cmd_string.endswith("\n"):
        cmd_string += "\n"

    # Prefix with ESC ESC to cancel any active command safely in-band
    full_cmd = "\x1b\x1b" + cmd_string
    cmd_bytes = full_cmd.encode('utf-16le') + b'\x00\x00'

    cds = COPYDATASTRUCT()
    cds.dwData = 1
    cds.cbData = len(cmd_bytes)
    cds.lpData = ctypes.cast(ctypes.c_char_p(cmd_bytes), ctypes.c_void_p)

    res = wintypes.DWORD()
    ret = user32.SendMessageTimeoutW(
        hwnd,
        WM_COPYDATA,
        0,
        ctypes.byref(cds),
        0x0002,
        30000,
        ctypes.byref(res)
    )
    return ret != 0, f"Result: {ret}"

# Test sending a command
test_file = r"d:/Dropbox/_Documents/RevitAI/scratch_sync_test.txt"
if os.path.exists(test_file):
    os.remove(test_file)

cmd = f'(progn (setq f (open "{test_file.replace(chr(92), "/")}" "w")) (write-line "HELLO_FROM_CLEAN_SEND" f) (close f))'
ok, msg = send_clean(cmd)
print("Send status:", ok, msg)

time.sleep(0.5)
if os.path.exists(test_file):
    with open(test_file) as f:
        print("File content:", f.read().strip())
else:
    print("File not created!")
