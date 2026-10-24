import os
import subprocess
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8')

def to_acad_unicode(s):
    res = []
    for char in s:
        cp = ord(char)
        if cp > 127:
            res.append(f'\\U+{cp:04X}')
        else:
            res.append(char)
    return ''.join(res)

dwg_dir = r"D:\Dropbox\_Documents\RevitAI\DWG_Export_Individual"
master_file = os.path.join(dwg_dir, "TEST_2COLUMNS.dwg")
shutil.copyfile(os.path.join(dwg_dir, "view_01.dwg"), master_file)

# 12 Views configuration
# Column 1: Floor plans (view_01 to view_07)
# Center X for floor plan is ~ 20,000mm. Axis 1..11: 0..38000.
# Step Y: 35,000mm
floor_plans = [
    ("view_01.dwg", 0.0, 0.0, "01. MẶT BẰNG TẦNG 1", 20000.0, -8000.0),
    ("view_02.dwg", 0.0, -35000.0, "02. MẶT BẰNG TẦNG 2", 20000.0, -43000.0),
    ("view_03.dwg", 0.0, -70000.0, "03. MẶT BẰNG TẦNG 3", 20000.0, -78000.0),
    ("view_04.dwg", 0.0, -105000.0, "04. MẶT BẰNG TẦNG 4", 20000.0, -113000.0),
    ("view_05.dwg", 0.0, -140000.0, "05. MẶT BẰNG TẦNG ÁP MÁI", 20000.0, -148000.0),
    ("view_06.dwg", 0.0, -175000.0, "06. MẶT BẰNG TẦNG TUM", 20000.0, -183000.0),
    ("view_07.dwg", 0.0, -210000.0, "07. MẶT BẰNG MÁI", 20000.0, -218000.0),
]

# Column 2: Sections (view_08 to view_12)
# X offset = 65,000mm
# Step Y: 32,000mm
sections = [
    ("view_08.dwg", 65000.0, 0.0, "MẶT CẮT 1-1", 65000.0 + 24000.0, -5000.0),
    ("view_09.dwg", 65000.0, -32000.0, "MẶT CẮT 2-2", 65000.0 + 24000.0, -37000.0),
    ("view_10.dwg", 65000.0, -64000.0, "MẶT CẮT 3-3", 65000.0 + 11000.0, -69000.0),
    ("view_11.dwg", 65000.0, -96000.0, "MẶT CẮT 4-4", 65000.0 + 11000.0, -101000.0),
    ("view_12.dwg", 65000.0, -128000.0, "MẶT CẮT 5-5", 65000.0 + 9000.0, -133000.0),
]

scr_lines = [
    "FILEDIA",
    "0",
    "CMDECHO",
    "1"
]

# Insert Floor Plans 2..7 (view_01 is base)
for fname, x_off, y_off, title, tx, ty in floor_plans[1:]:
    fpath = os.path.join(dwg_dir, fname).replace("\\", "/")
    scr_lines.extend([
        "_-INSERT",
        f"*{fpath}",
        f"{x_off:.0f},{y_off:.0f}",
        "1",
        "0"
    ])

# Insert Sections 1..5
for fname, x_off, y_off, title, tx, ty in sections:
    fpath = os.path.join(dwg_dir, fname).replace("\\", "/")
    scr_lines.extend([
        "_-INSERT",
        f"*{fpath}",
        f"{x_off:.0f},{y_off:.0f}",
        "1",
        "0"
    ])

# Setup Unicode Style
scr_lines.extend([
    "_-STYLE",
    "UNICODE_TITLE",
    "arial.ttf",
    "0",
    "1.0",
    "0",
    "_N",
    "_N"
])

# Add Titles for all 12 views
all_views = floor_plans + sections
for fname, x_off, y_off, title, tx, ty in all_views:
    encoded_title = to_acad_unicode(title)
    scr_lines.extend([
        "_-TEXT",
        "_S",
        "UNICODE_TITLE",
        "_J",
        "_MC",
        f"{tx:.0f},{ty:.0f}",
        "800",
        "0",
        encoded_title
    ])

# Layer colors
from export_views_vertical_dwg import WILDCARD_COLOR_RULES, STANDARD_LAYER_COLORS
for pattern, col in WILDCARD_COLOR_RULES:
    scr_lines.extend(["_-LAYER", "_C", str(col), pattern, ""])
for lay, col in STANDARD_LAYER_COLORS.items():
    scr_lines.extend(["_-LAYER", "_C", str(col), lay, ""])

# Zoom, Save, Quit
scr_lines.extend([
    "_ZOOM",
    "_E",
    "_QSAVE",
    "_QUIT"
])

scr_path = os.path.join(dwg_dir, "assemble_2columns.scr")
with open(scr_path, "w", encoding="ascii") as f:
    f.write("\n".join(scr_lines) + "\n")

accore = r"C:\Program Files\Autodesk\AutoCAD 2022\accoreconsole.exe"
cmd = [accore, "/i", master_file, "/s", scr_path]
print("Running AutoCAD Core Console 2-column assembly...")
proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=60)
print("Finished. Returncode:", proc.returncode)
print("Final size:", os.path.getsize(master_file), "bytes")
