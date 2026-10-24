import os
import sys

try:
    import win32com.client
    shell = win32com.client.Dispatch("WScript.Shell")
    desktop = shell.SpecialFolders("Desktop")
    project_dir = r"D:\Dropbox\_Documents\RevitAI"
    ico_path = os.path.join(project_dir, "revit_ai.ico")

    chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    edge = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    browser = chrome if os.path.exists(chrome) else edge

    # 1. Desktop shortcut
    desk_path = os.path.join(desktop, "RevitAI Studio.lnk")
    sc_desk = shell.CreateShortcut(desk_path)
    sc_desk.TargetPath = browser
    sc_desk.Arguments = "--app=http://127.0.0.1:5000"
    sc_desk.IconLocation = f"{ico_path},0"
    sc_desk.Description = "RevitAI Studio - CAD, 3ds Max, Revit Automation Hub"
    sc_desk.WorkingDirectory = project_dir
    sc_desk.Save()

    # 2. Local Project folder shortcut
    proj_path = os.path.join(project_dir, "RevitAI Studio.lnk")
    sc_proj = shell.CreateShortcut(proj_path)
    sc_proj.TargetPath = browser
    sc_proj.Arguments = "--app=http://127.0.0.1:5000"
    sc_proj.IconLocation = f"{ico_path},0"
    sc_proj.Description = "RevitAI Studio - CAD, 3ds Max, Revit Automation Hub"
    sc_proj.WorkingDirectory = project_dir
    sc_proj.Save()

    # 3. System Tray Launcher shortcut
    py_dir = os.path.dirname(sys.executable)
    pythonw = os.path.join(py_dir, "pythonw.exe")
    if not os.path.exists(pythonw):
        pythonw = sys.executable

    tray_script = os.path.join(project_dir, "revit_tray.py")
    tray_lnk = os.path.join(project_dir, "RevitAI_SystemTray.lnk")
    sc_tray = shell.CreateShortcut(tray_lnk)
    sc_tray.TargetPath = pythonw
    sc_tray.Arguments = f'"{tray_script}"'
    sc_tray.IconLocation = f"{ico_path},0"
    sc_tray.Description = "Khởi động RevitAI Icon khay hệ thống (Taskbar Tray)"
    sc_tray.WorkingDirectory = project_dir
    sc_tray.Save()

    print("Success: Created all 3 shortcuts with revit_ai.ico!")
    print(f"1. Desktop: {desk_path}")
    print(f"2. Project: {proj_path}")
    print(f"3. System Tray: {tray_lnk}")
except Exception as ex:
    print(f"Error: {ex}")
