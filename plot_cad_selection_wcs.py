import json
import matplotlib.pyplot as plt

with open(r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\selected_3walls_1door.json", "r", encoding="utf-8") as f:
    items = json.load(f)

def to_rvt(x, y):
    return (x + 70950.0) / 1000.0, (y + 1400406.0) / 1000.0

fig, ax = plt.subplots(figsize=(10, 10))

for it in items:
    layer = it['layer']
    color = 'blue' if layer == 'S5' else ('red' if layer == 'A-Door' else 'green')
    t = it['objectName']
    
    if t == 'AcDbLine':
        p1 = to_rvt(it['start'][0], it['start'][1])
        p2 = to_rvt(it['end'][0], it['end'][1])
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=color, linewidth=2)
    elif 'Polyline' in t or 'Arc' in t:
        # use bounding box
        b1 = to_rvt(it['bb_min'][0], it['bb_min'][1])
        b2 = to_rvt(it['bb_max'][0], it['bb_max'][1])
        if it.get('objectName') == 'AcDbLine':
            pass
        else:
            rect = plt.Rectangle((b1[0], b1[1]), b2[0]-b1[0], b2[1]-b1[1], fill=False, edgecolor=color, linewidth=1.5)
            ax.add_patch(rect)
    elif 'Text' in t:
        ins = to_rvt(it['insertion'][0], it['insertion'][1])
        ax.text(ins[0], ins[1], it['text'], color='purple', fontsize=14, fontweight='bold')

ax.set_aspect('equal')
ax.grid(True, linestyle=':', alpha=0.6)
ax.set_title("Selected 3 Walls and 1 Door D5 (Revit Coordinates)")
ax.set_xlabel("X (m)")
ax.set_ylabel("Y (m)")

out_png = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\cad_selection_wcs_plot.png"
plt.savefig(out_png, dpi=200, bbox_inches='tight')
print(f"Saved plot to {out_png}")
