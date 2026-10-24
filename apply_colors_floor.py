import os
import subprocess
import shutil

dwg_dir = r"D:\Dropbox\_Documents\RevitAI\DWG_Export_Individual"
project_dwg_dir = r"D:\Dropbox\_Documents\_KIEN TRUC 2026\CAX"
desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")

master_name = "MAT_BANG_TONG_HOP_HANG_DOC.dwg"
master_path = os.path.join(dwg_dir, master_name)

STANDARD_COLORS = {
    "A-WALL": 7,
    "A-WALL-CUT": 7,
    "S-COLS": 7,
    "S-BEAM": 7,
    "S-FRAM": 7,
    "S-FNDN": 7,
    "A-FLOR": 7,
    "A-FLOR-MCUT": 7,
    "A-DETL-WIDE": 7,
    
    "A-DOOR": 2,
    "A-DOOR-FRAM": 2,
    "S-STRS": 2,
    "S-STRS-MBND": 2,
    "A-FLOR-HRAL": 2,
    "A-FLOR-HRAL-MBND": 2,
    "A-ANNO-NOTE": 2,
    "G-ANNO-TEXT": 2,
    
    "P-SANR-FIXT": 3,
    "A-DOOR-IDEN": 3,
    "A-GLAZ-IDEN": 3,
    "S-STRS-IDEN": 3,
    "S-STRS-ANNO": 3,
    "A-GENM": 3,
    
    "A-GLAZ": 4,
    "A-DOOR-GLAZ": 4,
    
    "S-GRID": 1,
    "S-GRID-IDEN": 1,
    "G-ANNO-LEVL": 1,
    "A-ANNO-DIMS": 1,
    "A-ANNO-DIMS-75": 1,
    "A-ANNO-DIMS-100": 1,
    
    "G-ANNO-SYMB": 6,
    
    "A-WALL-PATT": 8,
    "A-FLOR-PATT": 8,
    "S-COLS-PATT": 8,
    "A-FLOR-LEVL": 8,
    "A-DETL": 8,
    "A-DETL-THIN": 8,
    "A-DETL-GENF": 8,
    "G-IMPT": 8,
    
    "0": 7,
    "Defpoints": 7
}

scr_path = os.path.join(dwg_dir, "apply_colors_floor.scr")
lines = [
    "FILEDIA",
    "0",
    "CMDECHO",
    "1"
]

for lay, col in STANDARD_COLORS.items():
    lines.extend([
        "_-LAYER",
        "_C",
        str(col),
        lay,
        ""
    ])

lines.extend([
    "_ZOOM",
    "_E",
    "_QSAVE",
    "_QUIT"
])

with open(scr_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

accoreconsole = r"C:\Program Files\Autodesk\AutoCAD 2022\accoreconsole.exe"
cmd = [accoreconsole, "/i", master_path, "/s", scr_path]

proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="ignore", timeout=30)
print("Floor colors update finished with code:", proc.returncode)

if os.path.exists(master_path):
    dest_project = os.path.join(project_dwg_dir, master_name)
    shutil.copyfile(master_path, dest_project)
    print(f"Copied updated floor plans to project: {dest_project}")
    
    dest_desktop = os.path.join(desktop_dir, master_name)
    shutil.copyfile(master_path, dest_desktop)
    print(f"Copied updated floor plans to Desktop: {dest_desktop}")
