import os
import subprocess
import shutil

dwg_dir = r"D:\Dropbox\_Documents\RevitAI\DWG_Export_Individual"
project_dwg_dir = r"D:\Dropbox\_Documents\_KIEN TRUC 2026\CAX"
desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")

master_name = "MAT_BANG_TONG_HOP_HANG_DOC.dwg"
master_temp = os.path.join(dwg_dir, master_name)

# 1. Base drawing is floor_01.dwg
shutil.copyfile(os.path.join(dwg_dir, "floor_01.dwg"), master_temp)

# All 7 floor plans and their positions
all_floors = [
    # (filename, y_offset, title, title_y)
    ("floor_01.dwg", 0.0, "01. MẶT BẰNG TẦNG 1", -8500.0),
    ("floor_02.dwg", -40000.0, "02. MẶT BẰNG TẦNG 2", -48500.0),
    ("floor_03.dwg", -80000.0, "03. MẶT BẰNG TẦNG 3", -88500.0),
    ("floor_04.dwg", -120000.0, "04. MẶT BẰNG TẦNG 4", -128500.0),
    ("floor_05.dwg", -160000.0, "05. MẶT BẰNG TẦNG ÁP MÁI", -168500.0),
    ("floor_06.dwg", -200000.0, "06. MẶT BẰNG TẦNG TUM", -208500.0),
    ("floor_07.dwg", -240000.0, "07. MẶT BẰNG MÁI", -248500.0),
]

scr_path = os.path.join(dwg_dir, "assemble_vertical_with_titles.scr")

lines = [
    "FILEDIA",
    "0",
    "CMDECHO",
    "1"
]

# Insert floors 2 to 7 (floor 1 is already the base)
for fname, y_off, title, title_y in all_floors[1:]:
    fpath = os.path.join(dwg_dir, fname).replace("\\", "/")
    lines.extend([
        "_-INSERT",
        f"*{fpath}",
        f"0,{y_off:.0f}",
        "1",
        "0"
    ])

# Add titles for all floors
# In AutoCAD: -TEXT J MC <pt> <height> <rotation> <text>
for fname, y_off, title, title_y in all_floors:
    # Use ASCII or clean title for script compatibility
    clean_title = title.encode('ascii', 'ignore').decode('ascii')
    if not clean_title.strip():
        clean_title = fname.replace(".dwg", "")
    lines.extend([
        "_-TEXT",
        "_J",
        "_MC",
        f"21800,{title_y:.0f}",
        "600",
        "0",
        title
    ])

lines.extend([
    "_ZOOM",
    "_E",
    "_QSAVE",
    "_QUIT"
])

# Save as UTF-8 or with BOM or system codepage
# In AutoCAD, UTF-8 text with BOM works for modern AutoCAD TEXT commands
with open(scr_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

accoreconsole = r"C:\Program Files\Autodesk\AutoCAD 2022\accoreconsole.exe"
cmd = [accoreconsole, "/i", master_temp, "/s", scr_path]

print("Running AutoCAD Core Console assembly with titles...")
proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="ignore", timeout=60)

with open(os.path.join(dwg_dir, "assembly_titles_log.txt"), "w", encoding="utf-8") as out:
    out.write(proc.stdout)

print("Assembly finished with code:", proc.returncode)

if os.path.exists(master_temp):
    final_size = os.path.getsize(master_temp) / (1024.0 * 1024.0)
    print(f"Master DWG created: {master_temp} ({final_size:.2f} MB)")
    
    dest_project = os.path.join(project_dwg_dir, master_name)
    shutil.copyfile(master_temp, dest_project)
    print(f"Copied to project: {dest_project}")
    
    dest_desktop = os.path.join(desktop_dir, master_name)
    shutil.copyfile(master_temp, dest_desktop)
    print(f"Copied to Desktop: {dest_desktop}")
