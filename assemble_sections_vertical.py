import os
import subprocess
import shutil

sec_dir = r"D:\Dropbox\_Documents\RevitAI\DWG_Export_Sections"
project_dwg_dir = r"D:\Dropbox\_Documents\_KIEN TRUC 2026\CAX"
desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")

master_name = "MAT_CAT_TONG_HOP_HANG_DOC.dwg"
master_temp = os.path.join(sec_dir, master_name)

# 1. Base drawing is section_01.dwg (MẶT CẮT 1-1)
shutil.copyfile(os.path.join(sec_dir, "section_01.dwg"), master_temp)

sections = [
    # (filename, y_offset, title, title_y)
    ("section_01.dwg", 0.0, "MẶT CẮT 1-1", -5500.0),
    ("section_02.dwg", -35000.0, "MẶT CẮT 2-2", -40500.0),
    ("section_03.dwg", -70000.0, "MẶT CẮT 3-3", -75500.0),
    ("section_04.dwg", -105000.0, "MẶT CẮT 4-4", -110500.0),
    ("section_05.dwg", -140000.0, "MẶT CẮT 5-5", -145500.0),
]

# Standard Layer Colors Dictionary
STANDARD_COLORS = {
    # Tường, cột, dầm, sàn cắt (Trắng - Nét cắt đậm 0.35-0.50mm)
    "A-WALL": 7,
    "A-WALL-CUT": 7,
    "S-COLS": 7,
    "S-BEAM": 7,
    "S-FRAM": 7,
    "S-FNDN": 7,
    "A-FLOR": 7,
    "A-FLOR-MCUT": 7,
    "A-DETL-WIDE": 7,
    
    # Cửa đi, khuôn cửa, thang, lan can, chữ ghi chú (Vàng - Nét vừa 0.20-0.25mm)
    "A-DOOR": 2,
    "A-DOOR-FRAM": 2,
    "S-STRS": 2,
    "S-STRS-MBND": 2,
    "A-FLOR-HRAL": 2,
    "A-FLOR-HRAL-MBND": 2,
    "A-ANNO-NOTE": 2,
    "G-ANNO-TEXT": 2,
    
    # Thiết bị vệ sinh, tag cửa, ký hiệu (Xanh lá - Nét thấy 0.15mm)
    "P-SANR-FIXT": 3,
    "A-DOOR-IDEN": 3,
    "A-GLAZ-IDEN": 3,
    "S-STRS-IDEN": 3,
    "S-STRS-ANNO": 3,
    "A-GENM": 3,
    
    # Cửa sổ, kính, vách kính (Cyan - Nét kính 0.15-0.20mm)
    "A-GLAZ": 4,
    "A-DOOR-GLAZ": 4,
    
    # Kích thước, trục định vị, cao độ (Đỏ - Nét mảnh 0.09mm)
    "S-GRID": 1,
    "S-GRID-IDEN": 1,
    "G-ANNO-LEVL": 1,
    "A-ANNO-DIMS": 1,
    "A-ANNO-DIMS-75": 1,
    "A-ANNO-DIMS-100": 1,
    
    # Ký hiệu cao độ / Section head (Magenta - Nét ký hiệu 0.25mm)
    "G-ANNO-SYMB": 6,
    
    # Hatch gạch lát, hatch bê tông, hatch tường, nét chi tiết mảnh, CAD link (Xám đậm - Nét siêu mảnh 0.05-0.09mm)
    "A-WALL-PATT": 8,
    "A-FLOR-PATT": 8,
    "S-COLS-PATT": 8,
    "A-FLOR-LEVL": 8,
    "A-DETL": 8,
    "A-DETL-THIN": 8,
    "A-DETL-GENF": 8,
    "G-IMPT": 8,
    
    # Mặc định
    "0": 7,
    "Defpoints": 7
}

scr_path = os.path.join(sec_dir, "assemble_sections.scr")

lines = [
    "FILEDIA",
    "0",
    "CMDECHO",
    "1"
]

# Insert sections 2 to 5 exploded
for fname, y_off, title, title_y in sections[1:]:
    fpath = os.path.join(sec_dir, fname).replace("\\", "/")
    lines.extend([
        "_-INSERT",
        f"*{fpath}",
        f"0,{y_off:.0f}",
        "1",
        "0"
    ])

# Add Title text for each section
for fname, y_off, title, title_y in sections:
    lines.extend([
        "_-TEXT",
        "_J",
        "_MC",
        f"16700,{title_y:.0f}",
        "600",
        "0",
        title
    ])

# Set Layer Colors according to standard
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
cmd = [accoreconsole, "/i", master_temp, "/s", scr_path]

print("Running AutoCAD Core Console section assembly and layer color standard...")
proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="ignore", timeout=60)

with open(os.path.join(sec_dir, "assembly_sections_log.txt"), "w", encoding="utf-8") as out:
    out.write(proc.stdout)

print("Assembly finished with code:", proc.returncode)

if os.path.exists(master_temp):
    final_size = os.path.getsize(master_temp) / (1024.0 * 1024.0)
    print(f"Master Section DWG created: {master_temp} ({final_size:.2f} MB)")
    
    dest_project = os.path.join(project_dwg_dir, master_name)
    shutil.copyfile(master_temp, dest_project)
    print(f"Copied to project: {dest_project}")
    
    dest_desktop = os.path.join(desktop_dir, master_name)
    shutil.copyfile(master_temp, dest_desktop)
    print(f"Copied to Desktop: {dest_desktop}")
else:
    print("Master Section DWG was not created!")
