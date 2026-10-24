import os
import ezdxf
from ezdxf.enums import TextEntityAlignment

def create_dxf_model(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    dxf_path = os.path.join(output_dir, "NhaCap4_BIM.dxf")
    
    doc = ezdxf.new("R2018")
    msp = doc.modelspace()
    
    # 1. Setup Layers with colors
    layers_def = [
        ("BIM_Nen", 8),      # Xám bê tông
        ("BIM_Tuong", 7),    # Trắng tường
        ("BIM_CuaDi", 34),   # Nâu gỗ
        ("BIM_CuaSo", 140),  # Xanh kính
        ("BIM_Mai", 150),    # Xanh xám ngói
    ]
    for lname, color in layers_def:
        doc.layers.add(name=lname, color=color)
        
    def add_box(layer, x0, x1, y0, y1, z0, z1):
        v = [
            (x0, y0, z0), # 0
            (x1, y0, z0), # 1
            (x1, y1, z0), # 2
            (x0, y1, z0), # 3
            (x0, y0, z1), # 4
            (x1, y0, z1), # 5
            (x1, y1, z1), # 6
            (x0, y1, z1), # 7
        ]
        faces = [
            (v[3], v[2], v[1], v[0]), # Bottom
            (v[4], v[5], v[6], v[7]), # Top
            (v[0], v[1], v[5], v[4]), # Front
            (v[2], v[3], v[7], v[6]), # Back
            (v[3], v[0], v[4], v[7]), # Left
            (v[1], v[2], v[6], v[5]), # Right
        ]
        for f in faces:
            msp.add_3dface(f, dxfattribs={"layer": layer})

    # --- 1. NỀN (BIM_Nen) ---
    add_box("BIM_Nen", 0, 11000, 0, 7200, -470, 0)
    
    # --- 2. TƯỜNG (BIM_Tuong) ---
    # Tường sau
    add_box("BIM_Tuong", 0, 11000, 7000, 7200, 0, 2800)
    # Tường hông trái
    add_box("BIM_Tuong", 0, 200, 200, 7000, 0, 2800)
    # Tường hông phải
    add_box("BIM_Tuong", 10800, 11000, 200, 7000, 0, 2800)
    # Tường mặt tiền (với khoảng hở cửa đi và cửa sổ)
    add_box("BIM_Tuong", 0, 1500, 0, 200, 0, 2800)
    add_box("BIM_Tuong", 1500, 4800, 0, 200, 2700, 2800) # Lanh tô cửa đi
    add_box("BIM_Tuong", 4800, 7500, 0, 200, 0, 2800)   # Giữa 2 cửa
    add_box("BIM_Tuong", 7500, 10000, 0, 200, 0, 350)    # Bậu dưới cửa sổ
    add_box("BIM_Tuong", 7500, 10000, 0, 200, 2700, 2800)# Lanh tô cửa sổ
    add_box("BIM_Tuong", 10000, 11000, 0, 200, 0, 2800) # Phải cửa sổ

    # --- 3. CỬA ĐI (BIM_CuaDi) ---
    add_box("BIM_CuaDi", 1500, 4800, 30, 170, 0, 2700)

    # --- 4. CỬA SỔ (BIM_CuaSo) ---
    add_box("BIM_CuaSo", 7500, 10000, 40, 160, 350, 2700)

    # --- 5. MÁI NHẬT (BIM_Mai) ---
    # 4 góc đáy
    p1 = (-1200, -1200, 2800)
    p2 = (12200, -1200, 2800)
    p3 = (12200, 8400, 2800)
    p4 = (-1200, 8400, 2800)
    # 2 điểm sống nóc
    r1 = (3600, 3600, 4940)
    r2 = (7400, 3600, 4940)

    # Đáy mái
    msp.add_3dface((p4, p3, p2, p1), dxfattribs={"layer": "BIM_Mai"})
    # Mái dốc trước (hình thang)
    msp.add_3dface((p1, p2, r2, r1), dxfattribs={"layer": "BIM_Mai"})
    # Mái dốc sau (hình thang)
    msp.add_3dface((p3, p4, r1, r2), dxfattribs={"layer": "BIM_Mai"})
    # Mái hồi trái (tam giác)
    msp.add_3dface((p4, p1, r1, r1), dxfattribs={"layer": "BIM_Mai"})
    # Mái hồi phải (tam giác)
    msp.add_3dface((p2, p3, r2, r2), dxfattribs={"layer": "BIM_Mai"})

    doc.saveas(dxf_path)
    print(f"Generated DXF: {dxf_path} ({os.path.getsize(dxf_path)} bytes)")
    return dxf_path

if __name__ == "__main__":
    out_dir = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads"
    create_dxf_model(out_dir)
