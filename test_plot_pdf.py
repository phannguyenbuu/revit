import os
import subprocess

dwg_path = r"D:\Dropbox\_Documents\RevitAI\DWG_Export_Individual\MAT_BANG_TONG_HOP_HANG_DOC.dwg"
pdf_path = r"D:\Dropbox\_Documents\RevitAI\DWG_Export_Individual\MAT_BANG_TONG_HOP_HANG_DOC.pdf"
pdf_fwd = pdf_path.replace("\\", "/")

scr_path = r"D:\Dropbox\_Documents\RevitAI\plot_to_pdf.scr"

# -PLOT
# Detailed plot configuration? [Yes/No] <No>: Y
# Enter a layout name or [?] <Model>: Model
# Enter an output device name or [?] <None>: DWG To PDF.pc3
# Enter paper size: ISO full bleed A0 (841.00 x 1189.00 MM)
# Enter drawing orientation [Portrait/Landscape] <Portrait>: P
# Plot upside down? [Yes/No] <No>: N
# Enter plot area [Display/Extents/Limits/View/Window] <Display>: E
# Enter plot scale (Plotted Millimeters=Drawing Units) or [Fit] <Fit>: F
# Enter plot offset (x,y) or [Center] <0.00,0.00>: C
# Plot with plot styles? [Yes/No] <Yes>: Y
# Enter plot style table name or [?] (enter . for none) <acad.ctb>: acad.ctb
# Plot with lineweights? [Yes/No] <Yes>: Y
# Enter shade plot setting [As displayed/Wireframe/Hidden/Visual styles/Rendered] <As displayed>: A
# Write the plot to a file [Yes/No] <N>: Y
# Enter file name: <path>
# Save changes to page setup [Yes/No]? <N> N
# Proceed with plot [Yes/No] <Y>: Y
scr_content = f"""FILEDIA
0
CMDECHO
1
-PLOT
Y
Model
DWG To PDF.pc3
ISO full bleed A0 (841.00 x 1189.00 MM)
P
N
E
F
C
Y
acad.ctb
Y
A
Y
"{pdf_fwd}"
N
Y
_.QUIT
_Y
"""

with open(scr_path, "w", encoding="ascii") as f:
    f.write(scr_content)

accoreconsole = r"C:\Program Files\Autodesk\AutoCAD 2022\accoreconsole.exe"
cmd = [accoreconsole, "/i", dwg_path, "/s", scr_path]

proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="ignore", timeout=30)
if os.path.exists(pdf_path):
    print(f"PDF successfully plotted! Size: {os.path.getsize(pdf_path)/1024:.1f} KB")
else:
    print("PDF was not created.")
