import os

def create_obj_and_mtl(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    obj_path = os.path.join(output_dir, "NhaCap4_BIM.obj")
    mtl_path = os.path.join(output_dir, "NhaCap4_BIM.mtl")
    
    # 1. Generate MTL (Materials)
    mtl_content = """# RevitAI - Materials for Nha Cap 4 BIM
# Standard Architectural PBR / Shading Definition

newmtl Mat_Nen
Ka 0.2 0.2 0.2
Kd 0.6 0.6 0.6
Ks 0.1 0.1 0.1
Ns 10.0
d 1.0
illum 2

newmtl Mat_Tuong
Ka 0.3 0.3 0.3
Kd 0.94 0.93 0.90
Ks 0.1 0.1 0.1
Ns 20.0
d 1.0
illum 2

newmtl Mat_CuaDi_Wood
Ka 0.2 0.1 0.05
Kd 0.45 0.22 0.10
Ks 0.3 0.3 0.3
Ns 40.0
d 1.0
illum 2

newmtl Mat_CuaDi_Glass
Ka 0.1 0.15 0.2
Kd 0.6 0.75 0.85
Ks 0.9 0.9 0.9
Ns 90.0
d 0.5
illum 4

newmtl Mat_CuaSo_Frame
Ka 0.1 0.1 0.1
Kd 0.2 0.2 0.2
Ks 0.4 0.4 0.4
Ns 50.0
d 1.0
illum 2

newmtl Mat_CuaSo_Glass
Ka 0.1 0.15 0.2
Kd 0.65 0.80 0.92
Ks 0.9 0.9 0.9
Ns 95.0
d 0.4
illum 4

newmtl Mat_Mai_Tile
Ka 0.1 0.15 0.2
Kd 0.20 0.28 0.36
Ks 0.2 0.2 0.2
Ns 30.0
d 1.0
illum 2
"""
    with open(mtl_path, "w", encoding="utf-8") as f:
        f.write(mtl_content)
        
    # 2. Build OBJ Vertices & Faces
    vertices = []
    normals = []
    
    # Normal vectors
    # 1: +Z, 2: -Z, 3: +Y, 4: -Y, 5: +X, 6: -X
    # plus roof slope normals
    normals = [
        (0.0, 0.0, 1.0),   # 1: Up
        (0.0, 0.0, -1.0),  # 2: Down
        (0.0, 1.0, 0.0),   # 3: Back
        (0.0, -1.0, 0.0),  # 4: Front
        (1.0, 0.0, 0.0),   # 5: Right
        (-1.0, 0.0, 0.0),  # 6: Left
    ]

    elements = [] # (group_name, material_name, faces_list)
    
    def add_box(group_name, material_name, x0, x1, y0, y1, z0, z1):
        # 8 vertices for axis-aligned box
        base_idx = len(vertices) + 1
        v = [
            (x0, y0, z0), # 1
            (x1, y0, z0), # 2
            (x1, y1, z0), # 3
            (x0, y1, z0), # 4
            (x0, y0, z1), # 5
            (x1, y0, z1), # 6
            (x1, y1, z1), # 7
            (x0, y1, z1), # 8
        ]
        vertices.extend(v)
        
        # 6 quad faces (v_idx, n_idx)
        # bottom (Z-), top (Z+), front (Y-), back (Y+), left (X-), right (X+)
        faces = [
            [(base_idx+3, 2), (base_idx+2, 2), (base_idx+1, 2), (base_idx+0, 2)], # bottom: 4, 3, 2, 1
            [(base_idx+4, 1), (base_idx+5, 1), (base_idx+6, 1), (base_idx+7, 1)], # top: 5, 6, 7, 8
            [(base_idx+0, 4), (base_idx+1, 4), (base_idx+5, 4), (base_idx+4, 4)], # front: 1, 2, 6, 5
            [(base_idx+2, 3), (base_idx+3, 3), (base_idx+7, 3), (base_idx+6, 3)], # back: 3, 4, 8, 7
            [(base_idx+3, 6), (base_idx+0, 6), (base_idx+4, 6), (base_idx+7, 6)], # left: 4, 1, 5, 8
            [(base_idx+1, 5), (base_idx+2, 5), (base_idx+6, 5), (base_idx+5, 5)], # right: 2, 3, 7, 6
        ]
        elements.append((group_name, material_name, faces))

    # --- 1. NỀN (BIM_Nen) ---
    # Kích thước: 11000 x 7200 x 470mm (-470mm -> 0mm)
    add_box("BIM_Nen", "Mat_Nen", 0, 11000, 0, 7200, -470, 0)
    
    # --- 2. TƯỜNG (BIM_Tuong) ---
    # Tường dày 200mm, cao 2800mm từ cốt 0.000
    # Back wall: Y: 7000..7200, X: 0..11000, Z: 0..2800
    add_box("BIM_Tuong", "Mat_Tuong", 0, 11000, 7000, 7200, 0, 2800)
    # Left wall: X: 0..200, Y: 200..7000, Z: 0..2800
    add_box("BIM_Tuong", "Mat_Tuong", 0, 200, 200, 7000, 0, 2800)
    # Right wall: X: 10800..11000, Y: 200..7000, Z: 0..2800
    add_box("BIM_Tuong", "Mat_Tuong", 10800, 11000, 200, 7000, 0, 2800)
    # Front wall segments (with openings for Cua_di at 1500..4800, Cua_so at 7500..10000)
    # Seg 1: X: 0..1500, Y: 0..200, Z: 0..2800
    add_box("BIM_Tuong", "Mat_Tuong", 0, 1500, 0, 200, 0, 2800)
    # Seg 2: Lanh tô trên cửa đi: X: 1500..4800, Y: 0..200, Z: 2700..2800
    add_box("BIM_Tuong", "Mat_Tuong", 1500, 4800, 0, 200, 2700, 2800)
    # Seg 3: Giữa cửa đi & cửa sổ: X: 4800..7500, Y: 0..200, Z: 0..2800
    add_box("BIM_Tuong", "Mat_Tuong", 4800, 7500, 0, 200, 0, 2800)
    # Seg 4: Bậu dưới cửa sổ: X: 7500..10000, Y: 0..200, Z: 0..350
    add_box("BIM_Tuong", "Mat_Tuong", 7500, 10000, 0, 200, 0, 350)
    # Seg 5: Lanh tô trên cửa sổ: X: 7500..10000, Y: 0..200, Z: 2700..2800
    add_box("BIM_Tuong", "Mat_Tuong", 7500, 10000, 0, 200, 2700, 2800)
    # Seg 6: Phải cửa sổ: X: 10000..11000, Y: 0..200, Z: 0..2800
    add_box("BIM_Tuong", "Mat_Tuong", 10000, 11000, 0, 200, 0, 2800)
    
    # --- 3. CỬA ĐI (BIM_CuaDi) ---
    # Cửa chính 4 cánh: X: 1500..4800, Y: 50..150, Z: 0..2700 (lùi vào giữa tường)
    # Khung cửa đi:
    add_box("BIM_CuaDi", "Mat_CuaDi_Wood", 1500, 4800, 30, 170, 0, 2700)
    # 4 Ô kính tạo điểm nhấn cho cửa chính
    for k in range(4):
        gx0 = 1500 + 100 + k * 800
        gx1 = gx0 + 600
        add_box("BIM_CuaDi", "Mat_CuaDi_Glass", gx0, gx1, 80, 120, 600, 2400)

    # --- 4. CỬA SỔ (BIM_CuaSo) ---
    # Cửa sổ kính: X: 7500..10000, Y: 40..160, Z: 350..2700
    # Khung cửa sổ:
    add_box("BIM_CuaSo", "Mat_CuaSo_Frame", 7500, 10000, 40, 160, 350, 2700)
    # Kính cửa sổ:
    for k in range(3):
        wx0 = 7500 + 80 + k * 800
        wx1 = wx0 + 640
        add_box("BIM_CuaSo", "Mat_CuaSo_Glass", wx0, wx1, 90, 110, 450, 2600)

    # --- 5. MÁI NHẬT (BIM_Mai) ---
    # Base: X: -1200..12200, Y: -1200..8400, Z: 2800
    # Ridge: X: 3600..7400, Y: 3600, Z: 4940
    # Add vertices for Mái Nhật
    roof_base = len(vertices) + 1
    # 4 base corners
    # 1: (-1200, -1200, 2800)
    # 2: (12200, -1200, 2800)
    # 3: (12200, 8400, 2800)
    # 4: (-1200, 8400, 2800)
    # 2 ridge vertices
    # 5: (3600, 3600, 4940)
    # 6: (7400, 3600, 4940)
    rv = [
        (-1200, -1200, 2800), # 1
        (12200, -1200, 2800), # 2
        (12200, 8400, 2800),  # 3
        (-1200, 8400, 2800),  # 4
        (3600, 3600, 4940),   # 5 (ridge left)
        (7400, 3600, 4940),   # 6 (ridge right)
    ]
    vertices.extend(rv)
    
    # Calculate normals for roof slopes
    # Front slope: (1, 2, 6, 5) -> vector 1->2 is (13400, 0, 0), 1->5 is (4800, 4800, 2140)
    # normal = (0, -2140, 4800)
    n_front_idx = len(normals) + 1
    normals.append((0.0, -0.407, 0.913))
    # Back slope: (3, 4, 5, 6) -> normal = (0, 2140, 4800)
    n_back_idx = len(normals) + 1
    normals.append((0.0, 0.407, 0.913))
    # Left hip: (4, 1, 5) -> normal = (-2140, 0, 4800)
    n_left_idx = len(normals) + 1
    normals.append((-0.407, 0.0, 0.913))
    # Right hip: (2, 3, 6) -> normal = (2140, 0, 4800)
    n_right_idx = len(normals) + 1
    normals.append((0.407, 0.0, 0.913))
    
    roof_faces = [
        # Soffit / bottom face: (4, 3, 2, 1) normal 2 (Down)
        [(roof_base+3, 2), (roof_base+2, 2), (roof_base+1, 2), (roof_base+0, 2)],
        # Front trapezoid slope: (1, 2, 6, 5)
        [(roof_base+0, n_front_idx), (roof_base+1, n_front_idx), (roof_base+5, n_front_idx), (roof_base+4, n_front_idx)],
        # Back trapezoid slope: (3, 4, 5, 6)
        [(roof_base+2, n_back_idx), (roof_base+3, n_back_idx), (roof_base+4, n_back_idx), (roof_base+5, n_back_idx)],
        # Left hip triangle: (4, 1, 5)
        [(roof_base+3, n_left_idx), (roof_base+0, n_left_idx), (roof_base+4, n_left_idx)],
        # Right hip triangle: (2, 3, 6)
        [(roof_base+1, n_right_idx), (roof_base+2, n_right_idx), (roof_base+5, n_right_idx)],
    ]
    elements.append(("BIM_Mai", "Mat_Mai_Tile", roof_faces))

    # 3. Write OBJ file
    with open(obj_path, "w", encoding="utf-8") as f:
        f.write("# RevitAI - 3D BIM Model: Nha Cap 4\n")
        f.write(f"mtllib {os.path.basename(mtl_path)}\n\n")
        
        # Vertices
        for vx, vy, vz in vertices:
            f.write(f"v {vx:.2f} {vy:.2f} {vz:.2f}\n")
        f.write("\n")
        
        # Normals
        for nx, ny, nz in normals:
            f.write(f"vn {nx:.4f} {ny:.4f} {nz:.4f}\n")
        f.write("\n")
        
        # Groups and Faces
        for grp_name, mat_name, f_list in elements:
            f.write(f"g {grp_name}\n")
            f.write(f"usemtl {mat_name}\n")
            for face in f_list:
                f_str = " ".join([f"{v_idx}//{n_idx}" for v_idx, n_idx in face])
                f.write(f"f {f_str}\n")
            f.write("\n")
            
    print(f"Generated OBJ: {obj_path} ({os.path.getsize(obj_path)} bytes)")
    print(f"Generated MTL: {mtl_path} ({os.path.getsize(mtl_path)} bytes)")
    return obj_path, mtl_path

if __name__ == "__main__":
    out_dir = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads"
    create_obj_and_mtl(out_dir)
