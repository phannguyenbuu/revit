import trimesh
import os
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

obj_dir = r"C:\Users\Admin\.gemini\antigravity\scratch\obj_export_meters"
files = ["wall.obj", "door.obj", "window.obj", "stair.obj"]
loaded = {}

for f in files:
    path = os.path.join(obj_dir, f)
    mesh = trimesh.load(path, force="mesh")
    loaded[f] = mesh
    bmin = mesh.bounds[0]
    bmax = mesh.bounds[1]
    print(f"[{f}]")
    print(f"  Vertices: {len(mesh.vertices):,}, Faces: {len(mesh.faces):,}")
    print(f"  X: [{bmin[0]:.2f}m to {bmax[0]:.2f}m] (Width = {bmax[0]-bmin[0]:.2f}m)")
    print(f"  Y: [{bmin[1]:.2f}m to {bmax[1]:.2f}m] (Depth = {bmax[1]-bmin[1]:.2f}m)")
    print(f"  Z: [{bmin[2]:.2f}m to {bmax[2]:.2f}m] (Height = {bmax[2]-bmin[2]:.2f}m)")

# Render isometric 3D view
fig = plt.figure(figsize=(18, 10), dpi=200)
ax = fig.add_subplot(111, projection="3d")
ax.set_facecolor("#181818")
fig.patch.set_facecolor("#181818")

colors = {
    "wall.obj": "#e0e0e0",
    "door.obj": "#2ecc71",
    "window.obj": "#00d2d3",
    "stair.obj": "#f39c12"
}

for name in ["wall.obj", "window.obj", "door.obj", "stair.obj"]:
    mesh = loaded[name]
    v = mesh.vertices
    f = mesh.faces
    step = max(1, len(f) // 1500)
    sample_f = f[::step]
    triangles = v[sample_f]
    coll = Poly3DCollection(triangles, facecolors=colors[name], edgecolors="#222222", linewidths=0.2, alpha=0.9)
    ax.add_collection3d(coll)

all_bounds = np.array([m.bounds for m in loaded.values()])
min_b = all_bounds[:, 0, :].min(axis=0)
max_b = all_bounds[:, 1, :].max(axis=0)

ax.set_xlim(min_b[0]-2, max_b[0]+2)
ax.set_ylim(min_b[1]-2, max_b[1]+2)
ax.set_zlim(0, 5.0)

ax.view_init(elev=40, azim=-55)
ax.set_title("Architectural 3D Model: Wall, Door, Window, Stair", color="white", fontsize=16, pad=20)
ax.set_xlabel("X (m)", color="gray")
ax.set_ylabel("Y (m)", color="gray")
ax.set_zlabel("Height (m)", color="gray")
ax.tick_params(colors="gray")
ax.grid(color="#333333", linestyle="--")

out_png = r"C:\Users\Admin\.gemini\antigravity\scratch\obj_3d_render.png"
plt.savefig(out_png, dpi=200, bbox_inches="tight", facecolor="#181818")
plt.close(fig)
print(f"\nRendered 3D preview successfully to: {out_png}")
