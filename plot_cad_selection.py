import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches

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
    elif 'Polyline' in t:
        coords = it['coords']
        pts = [to_rvt(c[0], c[1]) for c in coords]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        if it.get('closed', False):
            xs.append(xs[0])
            ys.append(ys[0])
        ax.plot(xs, ys, color=color, linewidth=1.5)
    elif 'Arc' in t:
        # draw bounding box of arc
        b1 = to_rvt(it['bb_min'][0], it['bb_min'][1])
        b2 = to_rvt(it['bb_max'][0], it['bb_max'][1])
        ax.plot([b1[0], b2[0], b2[0], b1[0], b1[0]], [b1[1], b1[1], b2[1], b2[1], b1[1]], color='orange', linestyle='--', linewidth=0.8)
    elif 'Text' in t:
        ins = to_rvt(it['insertion'][0], it['insertion'][1])
        ax.text(ins[0], ins[1], it['text'], color='purple', fontsize=12, fontweight='bold')

ax.set_aspect('equal')
ax.grid(True, linestyle=':', alpha=0.6)
ax.set_title("Selected Objects in AutoCAD (Revit Coordinates)")
ax.set_xlabel("X (meters)")
ax.set_ylabel("Y (meters)")

out_png = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\cad_selection_plot.png"
plt.savefig(out_png, dpi=200, bbox_inches='tight')
print(f"Saved plot to {out_png}")
