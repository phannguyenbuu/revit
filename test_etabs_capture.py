import time
import ctypes
from ctypes import wintypes
from PIL import ImageGrab
import comtypes.client
from comtypes.gen import ETABSv1

user32 = ctypes.windll.user32

def test_capture():
    edb_path = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads\test_clean_run.EDB"
    helper = comtypes.client.CreateObject('ETABSv1.Helper').QueryInterface(ETABSv1.cHelper)
    app = helper.CreateObjectProgId("CSI.ETABS.API.ETABSObject")
    app.ApplicationStart()
    app.Unhide()
    
    sap = app.SapModel
    sap.File.OpenFile(edb_path)
    
    time.sleep(3)
    
    # Find window
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    target_hwnd = None
    
    def enum_cb(hwnd, lparam):
        nonlocal target_hwnd
        if user32.IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(512)
            user32.GetWindowTextW(hwnd, buf, 512)
            if "etabs" in buf.value.lower() and "test_clean_run" in buf.value.lower():
                target_hwnd = hwnd
                return False
        return True
        
    user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
    print("Target HWND:", target_hwnd)
    
    if target_hwnd:
        # Bring to front & Maximize
        user32.ShowWindow(target_hwnd, 3) # SW_MAXIMIZE
        user32.SetForegroundWindow(target_hwnd)
        time.sleep(2)
        
        # Get Rect
        rect = wintypes.RECT()
        user32.GetWindowRect(target_hwnd, ctypes.byref(rect))
        bbox = (rect.left, rect.top, rect.right, rect.bottom)
        print("Capturing bbox:", bbox)
        
        img = ImageGrab.grab(bbox=bbox)
        save_path = r"d:\Dropbox\_Documents\RevitAI\scratch\etabs_direct_capture1.png"
        img.save(save_path)
        print("Saved capture to:", save_path)
        
    app.ApplicationExit(False)

if __name__ == "__main__":
    test_capture()
