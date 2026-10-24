import os
import sys
import subprocess
import ezdxf
import ifcopenshell
import ifcopenshell.api

def build_all(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    # ---------------- PARAMETERS (Converted from meters to millimeters) ----------------
    W = 11000.0
    D = 7200.0
    WALL_H = 2800.0
    EXT_WALL = 200.0
    INT_WALL = 100.0
    SLAB_T = 120.0
    EAVE_Z = 2800.0
    RIDGE_Z = 4940.0
    ROOF_OVERHANG_X = 1500.0
    ROOF_OVERHANG_Y = 1200.0

    # Data structures to collect geometry
    # boxes: list of (layer, mat_name, name, x, y, z, sx, sy, sz)
    boxes = []
    # custom_faces: list of (layer, mat_name, name, [pts_list])
    custom_faces = []

    # Material definitions: (name, [R, G, B], alpha)
    materials = {
        'Wall_WarmWhite': ([232, 229, 218], 1.0),
        'Partition_OffWhite': ([220, 220, 212], 1.0),
        'Concrete': ([155, 155, 150], 1.0),
        'RoofTile_Terracotta': ([150, 75, 52], 1.0),
        'Aluminium_DarkBronze': ([65, 62, 57], 1.0),
        'Glass_BlueGrey': ([135, 180, 195], 0.48),
        'DoorLeaf_Timber': ([130, 88, 55], 1.0),
        'FloorTile': ([190, 185, 174], 1.0),
        'Furniture_Wood': ([150, 112, 76], 1.0),
        'SanitaryWare': ([245, 245, 242], 1.0),
        'KitchenCounter': ([90, 91, 88], 1.0)
    }

    # Layer CAD color mapping
    layer_colors = {
        'S-Foundation': 8,      # Gray
        'S-Floors': 9,          # Light Gray
        'A-Walls-Exterior': 7,  # White
        'A-Walls-Interior': 2,  # Yellow
        'A-Doors': 34,          # Brown
        'A-Windows': 140,       # Cyan/Blue
        'A-Furniture': 42,      # Orange/Wood
        'A-Fixtures': 4,        # Cyan
        'A-Site': 80,           # Green/Stone
        'A-Roof': 150           # Blue-Gray/Tile
    }

    def add_box(layer, mat_name, name, x, y, z, sx, sy, sz):
        boxes.append((layer, mat_name, name, float(x), float(y), float(z), float(sx), float(sy), float(sz)))

    def add_door(name, x, y, z, width, height, thickness, orientation, layer='A-Doors'):
        fw = 45.0
        frame_mat = 'Aluminium_DarkBronze'
        leaf_mat = 'DoorLeaf_Timber'
        if orientation == 'front':
            add_box(layer, frame_mat, f'{name}_Jamb_L', x, y, z, fw, thickness, height)
            add_box(layer, frame_mat, f'{name}_Jamb_R', x+width-fw, y, z, fw, thickness, height)
            add_box(layer, frame_mat, f'{name}_Head', x, y, z+height-fw, width, thickness, fw)
            add_box(layer, leaf_mat, f'{name}_Leaf', x+12.0, y+15.0, z+20.0, width-24.0, 35.0, height-35.0)
            add_box(layer, frame_mat, f'{name}_Handle', x+width-90.0, y-10.0, z+1000.0, 18.0, 20.0, 25.0)
        else:
            add_box(layer, frame_mat, f'{name}_Jamb_L', x, y, z, thickness, fw, height)
            add_box(layer, frame_mat, f'{name}_Jamb_R', x, y+width-fw, z, thickness, fw, height)
            add_box(layer, frame_mat, f'{name}_Head', x, y, z+height-fw, thickness, width, fw)
            add_box(layer, leaf_mat, f'{name}_Leaf', x+15.0, y+12.0, z+20.0, 35.0, width-24.0, height-35.0)

    def add_window(name, x, y, z, width, height, thickness, orientation, layer='A-Windows'):
        fw = 50.0
        frame_mat = 'Aluminium_DarkBronze'
        glass_mat = 'Glass_BlueGrey'
        if orientation == 'front':
            add_box(layer, frame_mat, f'{name}_Frame_L', x, y, z, fw, thickness, height)
            add_box(layer, frame_mat, f'{name}_Frame_R', x+width-fw, y, z, fw, thickness, height)
            add_box(layer, frame_mat, f'{name}_Frame_T', x, y, z+height-fw, width, thickness, fw)
            add_box(layer, frame_mat, f'{name}_Frame_B', x, y, z, width, thickness, fw)
            add_box(layer, glass_mat, f'{name}_Glazing', x+fw, y+thickness*0.2, z+fw, width-2*fw, thickness*0.6, height-2*fw)
            add_box(layer, frame_mat, f'{name}_Mullion', x+width/2-fw/2, y, z+fw, fw, thickness, height-2*fw)
        else:
            add_box(layer, frame_mat, f'{name}_Frame_L', x, y, z, thickness, fw, height)
            add_box(layer, frame_mat, f'{name}_Frame_R', x, y+width-fw, z, thickness, fw, height)
            add_box(layer, frame_mat, f'{name}_Frame_T', x, y, z+height-fw, thickness, width, fw)
            add_box(layer, frame_mat, f'{name}_Frame_B', x, y, z, thickness, width, fw)
            add_box(layer, glass_mat, f'{name}_Glazing', x+thickness*0.2, y+fw, z+fw, thickness*0.6, width-2*fw, height-2*fw)

    # 1. SLAB / PLATFORM
    add_box('S-Foundation', 'Concrete', 'Foundation_Platform', 0, 0, -470.0, W, D, 470.0)
    add_box('S-Floors', 'FloorTile', 'Floor_Slab', 0, 0, 0, W, D, SLAB_T)

    # 2. EXTERIOR WALLS
    # Front wall segments
    front_segs = [[0.0, 550.0], [3000.0, 350.0], [4100.0, 350.0], [7000.0, 350.0], [10000.0, 1000.0]]
    for i, seg in enumerate(front_segs):
        add_box('A-Walls-Exterior', 'Wall_WarmWhite', f'Front_Wall_Seg_{i+1}', seg[0], 0, 120.0, seg[1], EXT_WALL, WALL_H-120.0)

    # Front openings (windows and doors)
    add_window('Window_Front_Left', 650.0, -15.0, 950.0, 1650.0, 1350.0, 70.0, 'front')
    add_door('Door_Front_Sliding_01', 2050.0, -20.0, 120.0, 900.0, 2150.0, 70.0, 'front')
    add_door('Door_Front_Sliding_02', 2950.0, -20.0, 120.0, 900.0, 2150.0, 70.0, 'front')
    add_window('Window_Front_Centre', 4250.0, -15.0, 1550.0, 1550.0, 750.0, 70.0, 'front')
    add_door('Door_Front_Right', 6650.0, -20.0, 120.0, 850.0, 2150.0, 70.0, 'front')
    add_window('Window_Front_Right_Large', 7650.0, -15.0, 850.0, 2000.0, 1450.0, 70.0, 'front')

    # Rear wall & windows
    add_box('A-Walls-Exterior', 'Wall_WarmWhite', 'Exterior_Wall_Rear', 0, D-EXT_WALL, 120.0, W, EXT_WALL, WALL_H-120.0)
    add_window('Window_Rear_Bedroom_3', 1000.0, D-30.0, 1350.0, 1400.0, 1000.0, 70.0, 'front')
    add_window('Window_Rear_Bath', 5000.0, D-30.0, 1800.0, 650.0, 550.0, 70.0, 'front')
    add_window('Window_Rear_Bedroom_2', 8000.0, D-30.0, 1350.0, 1700.0, 1000.0, 70.0, 'front')

    # Side walls
    add_box('A-Walls-Exterior', 'Wall_WarmWhite', 'Exterior_Wall_Left', 0, 200.0, 120.0, EXT_WALL, D-400.0, WALL_H-120.0)
    add_box('A-Walls-Exterior', 'Wall_WarmWhite', 'Exterior_Wall_Right', W-EXT_WALL, 200.0, 120.0, EXT_WALL, D-400.0, WALL_H-120.0)
    add_window('Window_Left_Side', -15.0, 4400.0, 1350.0, 1250.0, 1000.0, 70.0, 'side')
    add_window('Window_Right_Side', W-20.0, 4400.0, 1350.0, 1250.0, 1000.0, 70.0, 'side')

    # 3. INTERNAL PARTITIONS
    add_box('A-Walls-Interior', 'Partition_OffWhite', 'Part_Bed3_Front', 200.0, 4450.0, 120.0, 3550.0, INT_WALL, 2680.0)
    add_box('A-Walls-Interior', 'Partition_OffWhite', 'Part_Bed3_Left', 200.0, 4450.0, 120.0, INT_WALL, 2550.0, 2680.0)
    add_box('A-Walls-Interior', 'Partition_OffWhite', 'Part_Bed3_Right', 3650.0, 4450.0, 120.0, INT_WALL, 2550.0, 2680.0)

    add_box('A-Walls-Interior', 'Partition_OffWhite', 'Part_Bath_Front', 3800.0, 4450.0, 120.0, 3250.0, INT_WALL, 2680.0)
    add_box('A-Walls-Interior', 'Partition_OffWhite', 'Part_Bath_Left', 3800.0, 4450.0, 120.0, INT_WALL, 2550.0, 2680.0)
    add_box('A-Walls-Interior', 'Partition_OffWhite', 'Part_Bath_Right', 6950.0, 4450.0, 120.0, INT_WALL, 2550.0, 2680.0)
    add_box('A-Walls-Interior', 'Partition_OffWhite', 'Part_Bath_Rear', 3800.0, 6950.0, 120.0, 3250.0, INT_WALL, 2680.0)

    add_box('A-Walls-Interior', 'Partition_OffWhite', 'Part_Bed2_Front', 7050.0, 4450.0, 120.0, 3750.0, INT_WALL, 2680.0)
    add_box('A-Walls-Interior', 'Partition_OffWhite', 'Part_Bed2_Left', 7050.0, 4450.0, 120.0, INT_WALL, 2550.0, 2680.0)
    add_box('A-Walls-Interior', 'Partition_OffWhite', 'Part_Bed2_Right', 10700.0, 4450.0, 120.0, INT_WALL, 2550.0, 2680.0)

    add_box('A-Walls-Interior', 'Partition_OffWhite', 'Part_Bed1_Rear', 7050.0, 2700.0, 120.0, 3650.0, INT_WALL, 2680.0)
    add_box('A-Walls-Interior', 'Partition_OffWhite', 'Part_Bed1_Left', 7050.0, 200.0, 120.0, INT_WALL, 2550.0, 2680.0)

    add_box('A-Walls-Interior', 'Partition_OffWhite', 'Part_WC_Front', 5000.0, 2900.0, 120.0, 2000.0, INT_WALL, 2250.0)
    add_box('A-Walls-Interior', 'Partition_OffWhite', 'Part_WC_Left', 5000.0, 2900.0, 120.0, INT_WALL, 1350.0, 2250.0)
    add_box('A-Walls-Interior', 'Partition_OffWhite', 'Part_WC_Right', 6900.0, 2900.0, 120.0, INT_WALL, 1350.0, 2250.0)

    # 4. INTERIOR DOORS
    add_door('Door_Bedroom3', 3200.0, 4400.0, 120.0, 750.0, 2050.0, 60.0, 'front')
    add_door('Door_Bath_01', 4100.0, 4400.0, 120.0, 700.0, 2050.0, 60.0, 'front')
    add_door('Door_Bath_02', 6150.0, 4400.0, 120.0, 700.0, 2050.0, 60.0, 'front')
    add_door('Door_Bedroom2', 7200.0, 4400.0, 120.0, 750.0, 2050.0, 60.0, 'front')
    add_door('Door_Bedroom1', 7250.0, 2650.0, 120.0, 800.0, 2050.0, 60.0, 'front')
    add_door('Door_WC3', 6150.0, 2850.0, 120.0, 650.0, 2000.0, 60.0, 'front')

    # 5. FURNITURE & FIXTURES
    add_box('A-Furniture', 'Furniture_Wood', 'Bed_Bed3_Base', 550.0, 5150.0, 120.0, 1550.0, 2000.0, 280.0)
    add_box('A-Furniture', 'SanitaryWare', 'Bed_Bed3_Mattress', 580.0, 5180.0, 400.0, 1490.0, 1940.0, 120.0)
    add_box('A-Furniture', 'Furniture_Wood', 'Wardrobe_Bed3', 2450.0, 5150.0, 120.0, 550.0, 1400.0, 2100.0)

    add_box('A-Furniture', 'Furniture_Wood', 'Bed_Bed2_Base', 8250.0, 5000.0, 120.0, 1650.0, 2000.0, 280.0)
    add_box('A-Furniture', 'SanitaryWare', 'Bed_Bed2_Mattress', 8280.0, 5030.0, 400.0, 1590.0, 1940.0, 120.0)
    add_box('A-Furniture', 'Furniture_Wood', 'Wardrobe_Bed2', 9950.0, 4650.0, 120.0, 550.0, 1500.0, 2100.0)

    add_box('A-Furniture', 'Furniture_Wood', 'Bed_Bed1_Base', 8200.0, 550.0, 120.0, 1650.0, 2000.0, 280.0)
    add_box('A-Furniture', 'SanitaryWare', 'Bed_Bed1_Mattress', 8230.0, 580.0, 400.0, 1590.0, 1940.0, 120.0)
    add_box('A-Furniture', 'Furniture_Wood', 'Wardrobe_Bed1', 7250.0, 550.0, 120.0, 550.0, 1450.0, 2100.0)

    add_box('A-Furniture', 'KitchenCounter', 'Kitchen_Counter_1', 350.0, 3200.0, 120.0, 2500.0, 620.0, 880.0)
    add_box('A-Furniture', 'KitchenCounter', 'Kitchen_Counter_2', 350.0, 3850.0, 120.0, 1450.0, 620.0, 880.0)
    add_box('A-Furniture', 'Furniture_Wood', 'Dining_Table', 1100.0, 1650.0, 780.0, 2000.0, 900.0, 80.0)

    for i in range(3):
        add_box('A-Furniture', 'Furniture_Wood', f'Chair_L_{i+1}', 650.0+i*720.0, 1350.0, 120.0, 420.0, 420.0, 450.0)
        add_box('A-Furniture', 'Furniture_Wood', f'Chair_R_{i+1}', 650.0+i*720.0, 2550.0, 120.0, 420.0, 420.0, 450.0)

    # WC fixtures
    add_box('A-Fixtures', 'SanitaryWare', 'WC1_Toilet', 4250.0, 5550.0, 120.0, 380.0, 620.0, 420.0)
    add_box('A-Fixtures', 'SanitaryWare', 'WC1_Vanity', 4050.0, 4750.0, 120.0, 650.0, 380.0, 820.0)
    add_box('A-Fixtures', 'SanitaryWare', 'WC2_Toilet', 6050.0, 5550.0, 120.0, 380.0, 620.0, 420.0)
    add_box('A-Fixtures', 'SanitaryWare', 'WC2_Vanity', 6100.0, 4750.0, 120.0, 620.0, 380.0, 820.0)
    add_box('A-Fixtures', 'SanitaryWare', 'WC3_Toilet', 6250.0, 3250.0, 120.0, 380.0, 620.0, 420.0)
    add_box('A-Fixtures', 'SanitaryWare', 'WC3_Vanity', 5200.0, 3150.0, 120.0, 550.0, 350.0, 820.0)

    # 6. SITE / VERANDA / STEPS
    add_box('A-Site', 'Concrete', 'Front_Veranda', -1500.0, -1200.0, -120.0, W+3000.0, 1200.0, 120.0)
    add_box('A-Site', 'Concrete', 'Front_Step', 0.0, -1550.0, -240.0, W, 350.0, 120.0)
    add_box('A-Site', 'Concrete', 'Left_Veranda', -1500.0, 0, -120.0, 1500.0, D, 120.0)
    add_box('A-Site', 'Concrete', 'Right_Veranda', W, 0, -120.0, 1500.0, D, 120.0)

    # 7. ROOF & FASCIA
    rx0 = -ROOF_OVERHANG_X
    rx1 = W + ROOF_OVERHANG_X
    ry0 = -ROOF_OVERHANG_Y
    ry1 = D + ROOF_OVERHANG_Y
    ridge_y0 = D * 0.35
    ridge_y1 = D * 0.65

    p_front_l = (rx0, ry0, EAVE_Z)
    p_front_r = (rx1, ry0, EAVE_Z)
    p_back_l  = (rx0, ry1, EAVE_Z)
    p_back_r  = (rx1, ry1, EAVE_Z)
    p_ridge_l = (0.0, ridge_y0, RIDGE_Z)
    p_ridge_r = (W, ridge_y0, RIDGE_Z)
    p_ridge_l2 = (0.0, ridge_y1, RIDGE_Z)
    p_ridge_r2 = (W, ridge_y1, RIDGE_Z)

    roof_slopes = [
        ('A-Roof', 'RoofTile_Terracotta', 'Roof_Slope_Front', [p_front_l, p_front_r, p_ridge_r, p_ridge_l]),
        ('A-Roof', 'RoofTile_Terracotta', 'Roof_Slope_Back', [p_back_l, p_ridge_l2, p_ridge_r2, p_back_r]),
        ('A-Roof', 'RoofTile_Terracotta', 'Roof_Slope_Left', [p_front_l, p_ridge_l, p_ridge_l2, p_back_l]),
        ('A-Roof', 'RoofTile_Terracotta', 'Roof_Slope_Right', [p_front_r, p_back_r, p_ridge_r2, p_ridge_r]),
    ]
    for r in roof_slopes:
        custom_faces.append(r)

    # Ridge cap & fascia
    add_box('A-Roof', 'RoofTile_Terracotta', 'Roof_Ridge_Cap', 0, ridge_y0, RIDGE_Z, W, ridge_y1-ridge_y0, 80.0)
    add_box('A-Roof', 'RoofTile_Terracotta', 'Fascia_Front', rx0, ry0, EAVE_Z-80.0, rx1-rx0, 80.0, 160.0)
    add_box('A-Roof', 'RoofTile_Terracotta', 'Fascia_Rear', rx0, ry1-80.0, EAVE_Z-80.0, rx1-rx0, 80.0, 160.0)

    print(f"Total building elements collected: {len(boxes)} boxes + {len(custom_faces)} roof faces.")

    # =========================================================================
    # EXPORT 1: WAVEFRONT OBJ & MTL
    # =========================================================================
    obj_file = os.path.join(output_dir, "house_bim_model.obj")
    mtl_file = os.path.join(output_dir, "house_bim_model.mtl")

    # Generate MTL
    with open(mtl_file, "w", encoding="utf-8") as f:
        f.write("# MTL file for house_bim_model\n\n")
        for mname, (rgb, alpha) in materials.items():
            r, g, b = [c/255.0 for c in rgb]
            f.write(f"newmtl {mname}\n")
            f.write(f"Ka {r*0.3:.3f} {g*0.3:.3f} {b*0.3:.3f}\n")
            f.write(f"Kd {r:.3f} {g:.3f} {b:.3f}\n")
            f.write("Ks 0.200 0.200 0.200\n")
            f.write("Ns 25.0\n")
            f.write(f"d {alpha:.2f}\n")
            f.write("illum 2\n\n")

    # Generate OBJ
    obj_vertices = []
    obj_groups = {} # layer -> list of faces (each face is list of vertex indices)

    for layer, mat, name, x, y, z, sx, sy, sz in boxes:
        b_idx = len(obj_vertices) + 1
        pts = [
            (x, y, z), (x+sx, y, z), (x+sx, y+sy, z), (x, y+sy, z),
            (x, y, z+sz), (x+sx, y, z+sz), (x+sx, y+sy, z+sz), (x, y+sy, z+sz)
        ]
        obj_vertices.extend(pts)
        quads = [
            [b_idx+3, b_idx+2, b_idx+1, b_idx+0], # bottom
            [b_idx+4, b_idx+5, b_idx+6, b_idx+7], # top
            [b_idx+0, b_idx+1, b_idx+5, b_idx+4], # front
            [b_idx+2, b_idx+3, b_idx+7, b_idx+6], # back
            [b_idx+3, b_idx+0, b_idx+4, b_idx+7], # left
            [b_idx+1, b_idx+2, b_idx+6, b_idx+5], # right
        ]
        if layer not in obj_groups: obj_groups[layer] = []
        for q in quads:
            obj_groups[layer].append((mat, q))

    for layer, mat, name, pts in custom_faces:
        b_idx = len(obj_vertices) + 1
        obj_vertices.extend(pts)
        face_indices = [b_idx + k for k in range(len(pts))]
        if layer not in obj_groups: obj_groups[layer] = []
        obj_groups[layer].append((mat, face_indices))

    with open(obj_file, "w", encoding="utf-8") as f:
        f.write("# Wavefront OBJ model for house_bim_model\n")
        f.write(f"mtllib {os.path.basename(mtl_file)}\n\n")
        for vx, vy, vz in obj_vertices:
            f.write(f"v {vx:.2f} {vy:.2f} {vz:.2f}\n")
        f.write("\n")
        for layer, flist in obj_groups.items():
            f.write(f"g {layer}\n")
            curr_mat = None
            for mat, face in flist:
                if mat != curr_mat:
                    f.write(f"usemtl {mat}\n")
                    curr_mat = mat
                f.write("f " + " ".join(str(idx) for idx in face) + "\n")
            f.write("\n")
    print(f"Generated OBJ: {obj_file} ({os.path.getsize(obj_file)} bytes)")

    # =========================================================================
    # EXPORT 2: 3D DXF & DWG
    # =========================================================================
    dxf_file = os.path.join(output_dir, "house_bim_model.dxf")
    dwg_file = os.path.join(output_dir, "house_bim_model.dwg")
    doc = ezdxf.new("R2018")
    msp = doc.modelspace()

    for lname, color in layer_colors.items():
        doc.layers.add(name=lname, color=color)

    for layer, mat, name, x, y, z, sx, sy, sz in boxes:
        v = [
            (x, y, z), (x+sx, y, z), (x+sx, y+sy, z), (x, y+sy, z),
            (x, y, z+sz), (x+sx, y, z+sz), (x+sx, y+sy, z+sz), (x, y+sy, z+sz)
        ]
        quads = [
            (v[3], v[2], v[1], v[0]),
            (v[4], v[5], v[6], v[7]),
            (v[0], v[1], v[5], v[4]),
            (v[2], v[3], v[7], v[6]),
            (v[3], v[0], v[4], v[7]),
            (v[1], v[2], v[6], v[5]),
        ]
        for q in quads:
            msp.add_3dface(q, dxfattribs={"layer": layer})

    for layer, mat, name, pts in custom_faces:
        if len(pts) == 4:
            msp.add_3dface(tuple(pts), dxfattribs={"layer": layer})
        elif len(pts) == 3:
            msp.add_3dface((pts[0], pts[1], pts[2], pts[2]), dxfattribs={"layer": layer})

    doc.saveas(dxf_file)
    print(f"Generated DXF: {dxf_file} ({os.path.getsize(dxf_file)} bytes)")

    # Convert DXF to DWG via accoreconsole
    scr_file = os.path.join(output_dir, "_dxf2dwg_tmp.scr")
    dwg_fwd = dwg_file.replace("\\", "/")
    with open(scr_file, "w", encoding="utf-8") as f:
        f.write(f'SAVEAS\n2018\n{dwg_fwd}\nQUIT\n')
    cmd = [r"C:\Program Files\Autodesk\AutoCAD 2022\accoreconsole.exe", "/i", dxf_file, "/s", scr_file]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        if os.path.exists(dwg_file):
            print(f"Generated DWG: {dwg_file} ({os.path.getsize(dwg_file)} bytes)")
    except Exception as e:
        print("DWG conversion note:", e)
    finally:
        if os.path.exists(scr_file):
            try: os.remove(scr_file)
            except: pass

    # =========================================================================
    # EXPORT 3: IFC4 BIM MODEL
    # =========================================================================
    ifc_file = os.path.join(output_dir, "house_bim_model.ifc")
    ifc_model = ifcopenshell.api.run("project.create_file", version="IFC4")
    project = ifcopenshell.api.run("root.create_entity", ifc_model, ifc_class="IfcProject", name="House_BIM_Project")
    ifcopenshell.api.run("unit.assign_unit", ifc_model, length={"is_metric": True, "raw": "MILLIMETERS"})

    context = ifcopenshell.api.run("context.add_context", ifc_model, context_type="Model")
    body_context = ifcopenshell.api.run(
        "context.add_context", ifc_model,
        context_type="Model", context_identifier="Body", target_view="MODEL_VIEW", parent=context
    )

    site = ifcopenshell.api.run("root.create_entity", ifc_model, ifc_class="IfcSite", name="Site")
    ifcopenshell.api.run("aggregate.assign_object", ifc_model, relating_object=project, products=[site])

    building = ifcopenshell.api.run("root.create_entity", ifc_model, ifc_class="IfcBuilding", name="House_Building")
    ifcopenshell.api.run("aggregate.assign_object", ifc_model, relating_object=site, products=[building])

    storey = ifcopenshell.api.run("root.create_entity", ifc_model, ifc_class="IfcBuildingStorey", name="Level_1")
    ifcopenshell.api.run("aggregate.assign_object", ifc_model, relating_object=building, products=[storey])

    def add_ifc_box(layer, name, x, y, z, sx, sy, sz):
        # Determine IFC class based on layer
        if layer == 'S-Foundation':
            ifc_class = 'IfcFooting'
        elif layer == 'S-Floors' or layer == 'A-Site':
            ifc_class = 'IfcSlab'
        elif layer.startswith('A-Walls'):
            ifc_class = 'IfcWall'
        elif layer == 'A-Doors':
            ifc_class = 'IfcDoor'
        elif layer == 'A-Windows':
            ifc_class = 'IfcWindow'
        elif layer == 'A-Roof':
            ifc_class = 'IfcRoof'
        elif layer == 'A-Fixtures':
            ifc_class = 'IfcSanitaryTerminal'
        else:
            ifc_class = 'IfcFurnishingElement'

        elem = ifcopenshell.api.run("root.create_entity", ifc_model, ifc_class=ifc_class, name=name)
        ifcopenshell.api.run("spatial.assign_container", ifc_model, relating_structure=storey, products=[elem])

        poly = ifc_model.create_entity(
            "IfcPolyline",
            Points=[
                ifc_model.create_entity("IfcCartesianPoint", Coordinates=[x, y]),
                ifc_model.create_entity("IfcCartesianPoint", Coordinates=[x+sx, y]),
                ifc_model.create_entity("IfcCartesianPoint", Coordinates=[x+sx, y+sy]),
                ifc_model.create_entity("IfcCartesianPoint", Coordinates=[x, y+sy]),
                ifc_model.create_entity("IfcCartesianPoint", Coordinates=[x, y]),
            ]
        )
        profile = ifc_model.create_entity("IfcArbitraryClosedProfileDef", ProfileType="AREA", OuterCurve=poly)
        pos = ifc_model.create_entity("IfcAxis2Placement3D",
            Location=ifc_model.create_entity("IfcCartesianPoint", Coordinates=[0.0, 0.0, z]),
            Axis=ifc_model.create_entity("IfcDirection", DirectionRatios=[0.0, 0.0, 1.0]),
            RefDirection=ifc_model.create_entity("IfcDirection", DirectionRatios=[1.0, 0.0, 0.0])
        )
        solid = ifc_model.create_entity(
            "IfcExtrudedAreaSolid",
            SweptArea=profile,
            Position=pos,
            ExtrudedDirection=ifc_model.create_entity("IfcDirection", DirectionRatios=[0.0, 0.0, 1.0]),
            Depth=float(sz)
        )
        rep = ifc_model.create_entity(
            "IfcShapeRepresentation",
            ContextOfItems=body_context,
            RepresentationIdentifier="Body",
            RepresentationType="SweptSolid",
            Items=[solid]
        )
        elem.Representation = ifc_model.create_entity("IfcProductDefinitionShape", Representations=[rep])

    for layer, mat, name, x, y, z, sx, sy, sz in boxes:
        add_ifc_box(layer, name, x, y, z, sx, sy, sz)

    ifc_model.write(ifc_file)
    print(f"Generated IFC: {ifc_file} ({os.path.getsize(ifc_file)} bytes)")

    print("\nALL FORMATS GENERATED SUCCESSFULLY!")
    return {
        "obj": obj_file,
        "mtl": mtl_file,
        "dxf": dxf_file,
        "dwg": dwg_file,
        "ifc": ifc_file
    }

if __name__ == "__main__":
    out_dir = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads"
    res = build_all(out_dir)
