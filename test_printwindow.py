import time
import ctypes
from ctypes import wintypes
from PIL import Image
import comtypes.client
from comtypes.gen import ETABSv1

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

def capture_hwnd_to_file(hwnd, save_path):
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    w = rect.right - rect.left
    h = rect.bottom - rect.top
    if w <= 0 or h <= 0:
        print("Invalid window size:", w, h)
        return False
        
    hwnd_dc = user32.GetWindowDC(hwnd)
    mem_dc = gdi32.CreateCompatibleDC(hwnd_dc)
    bitmap = gdi32.CreateCompatibleBitmap(hwnd_dc, w, h)
    old_bmp = gdi32.SelectObject(mem_dc, bitmap)
    
    # PW_RENDERFULLCONTENT = 2, PW_CLIENTONLY = 1
    # Try PW_RENDERFULLCONTENT first, fallback to 0
    ret = user32.PrintWindow(hwnd, mem_dc, 2)
    if not ret:
        ret = user32.PrintWindow(hwnd, mem_dc, 0)
        
    print(f"PrintWindow return: {ret}, size: {w}x{h}")
    
    # Convert bitmap to PIL Image
    # BITMAPINFOHEADER
    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ('biSize', wintypes.DWORD),
            ('biWidth', wintypes.LONG),
            ('biHeight', wintypes.LONG),
            ('biPlanes', wintypes.WORD),
            ('biBitCount', wintypes.WORD),
            ('biCompression', wintypes.DWORD),
            ('biSizeImage', wintypes.DWORD),
            ('biXPelsPerMeter', wintypes.LONG),
            ('biYPelsPerMeter', wintypes.LONG),
            ('biClrUsed', wintypes.DWORD),
            ('biClrImportant', wintypes.DWORD)
        ]
        
    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = w
    bmi.biHeight = -h # top-down
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0
    
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(mem_dc, bitmap, 0, h, buf, ctypes.byref(bmi), 0)
    
    img = Image.frombuffer('RGBA', (w, h), buf, 'raw', 'BGRA', 0, 1)
    img = img.convert('RGB')
    img.save(save_path)
    print("Saved image successfully to:", save_path)
    
    gdi32.SelectObject(mem_dc, old_bmp)
    gdi32.DeleteObject(bitmap)
    gdi32.DeleteDC(mem_dc)
    user32.ReleaseDC(hwnd, hwnd_dc)
    return True

def test_printwindow():
    edb_path = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads\test_clean_run.EDB"
    helper = comtypes.client.CreateObject('ETABSv1.Helper').QueryInterface(ETABSv1.cHelper)
    app = helper.CreateObjectProgId("CSI.ETABS.API.ETABSObject")
    app.ApplicationStart()
    app.Unhide()
    
    sap = app.SapModel
    sap.File.OpenFile(edb_path)
    time.sleep(3)
    
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
        # Resize window to 1600x900 for clean high-res capture
        user32.SetWindowPos(target_hwnd, 0, 50, 50, 1600, 900, 0x0040)
        time.sleep(2)
        save_path = r"d:\Dropbox\_Documents\RevitAI\scratch\etabs_printwindow_direct.png"
        capture_hwnd_to_file(target_hwnd, save_path)
        
    app.ApplicationExit(False)

if __name__ == "__main__":
    test_printwindow()
