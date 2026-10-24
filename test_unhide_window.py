import time
import comtypes.client
from comtypes.gen import ETABSv1
import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

def test_unhide_and_inspect():
    edb_path = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads\test_clean_run.EDB"
    helper = comtypes.client.CreateObject('ETABSv1.Helper').QueryInterface(ETABSv1.cHelper)
    app = helper.CreateObjectProgId("CSI.ETABS.API.ETABSObject")
    app.ApplicationStart()
    app.Unhide()
    print("Application started and unhidden.")
    
    sap = app.SapModel
    sap.File.OpenFile(edb_path)
    print("Model opened. Current file:", sap.GetModelFilename())
    print("Is locked (analyzed):", sap.GetModelIsLocked())
    
    time.sleep(3)
    
    # Find ETABS window
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    etabs_windows = []
    def enum_cb(hwnd, lparam):
        if user32.IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(512)
            user32.GetWindowTextW(hwnd, buf, 512)
            if "etabs" in buf.value.lower() or "cai tao" in buf.value.lower() or "phan boi chau" in buf.value.lower():
                etabs_windows.append((hwnd, buf.value))
        return True
    user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
    print("Found ETABS windows:", etabs_windows)

    # Keep alive for testing or exit
    app.ApplicationExit(False)

if __name__ == "__main__":
    test_unhide_and_inspect()
