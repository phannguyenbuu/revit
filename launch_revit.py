import subprocess
import os

revit_exe = r"C:\Program Files\Autodesk\Revit 2025\Revit.exe"
model_path = r"D:\Dropbox\_Documents\_KIEN TRUC 2026\CAX\Mau_40_CBS_Long_Tien.rvt"

if os.path.exists(revit_exe):
    print("Launching Revit...")
    proc = subprocess.Popen([revit_exe, model_path], cwd=r"C:\Program Files\Autodesk\Revit 2025")
    print("Process started with PID:", proc.pid)
else:
    print("Revit executable not found at:", revit_exe)
