import win32gui
import win32process
import psutil

def get_revit_windows():
    revit_pids = [p.pid for p in psutil.process_iter(['pid', 'name']) if 'revit' in (p.info['name'] or '').lower()]
    print(f"Revit PIDs: {revit_pids}")
    
    def cb(hwnd, results):
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if pid in revit_pids:
            title = win32gui.GetWindowText(hwnd)
            visible = win32gui.IsWindowVisible(hwnd)
            results.append((hwnd, visible, title))
            
    res = []
    win32gui.EnumWindows(cb, res)
    for h, v, t in res:
        print(f"HWND: {h} | Visible: {v} | Title: '{t}'")

if __name__ == "__main__":
    get_revit_windows()
