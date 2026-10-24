# --- Auto-Transpiled from SketchUp Ruby ---
import math
Math = math
model = Sketchup.active_model()
entities = model.entities
materials = model.materials
layers = model.layers

# -*- coding: UTF-8 -*-
# SketchUp Ruby API - mô hình nhà 1 tầng theo bản vẽ người dùng cung cấp
# Đơn vị dựng: mét quy đổi sang inch nội bộ SketchUp bằng .m
# Cách dùng: lưu file .rb, mở SketchUp > Window > Ruby Console,
# nhập: load 'C:/duong_dan/house_bim_model.rb'
#
# LƯU Ý:
# - Đây là mô hình kiến trúc sơ bộ để phát triển BIM, không thay thế hồ sơ thi công.
# - Một số kích thước/chi tiết trên ảnh không đọc được hoàn toàn; vị trí cửa, vách
#   và đồ nội thất được dựng gần đúng, có thể chỉnh tại phần PARAMETERS.
# - Tường được chia đoạn quanh ô cửa để tạo lỗ mở thật (không chỉ vẽ cửa chồng lên tường).
# - Các cấu kiện được nhóm riêng và gán Tag để dễ quản lý/xuất IFC qua extension phù hợp.

class _Mod_HouseBIMModel(RubyModule): pass
HouseBIMModel = _Mod_HouseBIMModel('HouseBIMModel', globals())
# extend self

# ---------------- PARAMETERS ----------------
# Hệ trục: X = ngang mặt tiền 11.0m; Y = chiều sâu nhà 7.2m; Z = cao độ.
# Khối nhà chính: 11 x 7.2m; mái đua khoảng 1.5m.
W = (11.0 * 1.0)
D = (7.2 * 1.0)
WALL_H = (2.8 * 1.0)
EXT_WALL = (0.2 * 1.0)
INT_WALL = (0.1 * 1.0)
SLAB_T = (0.12 * 1.0)
EAVE_Z = (2.8 * 1.0)
RIDGE_Z = (4.94 * 1.0)
ROOF_OVERHANG_X = (1.5 * 1.0)
ROOF_OVERHANG_Y = (1.2 * 1.0)

def tag(name, *extra_args):
    model = Sketchup.active_model()
    return model.layers[name]  or  model.layers.add(name)
# end (def)

def material(name, color, alpha = 1.0, *extra_args):
    mats = Sketchup.active_model().materials
    m = mats[name]  or  mats.add(name)
    m.color = Color(*color)
    m.alpha = alpha
    return m
# end (def)

def group(parent, name, layer_name = None, *extra_args):
    g = parent.add_group()
    g.name = name
    if layer_name: g.layer = tag(layer_name)
    return g
# end (def)

def face_box(entities, x, y, z, sx, sy, sz, mat = None, name = None, layer_name = None, *extra_args):
    g = entities.add_group()
    if name: g.name = name
    if layer_name: g.layer = tag(layer_name)
    pts = [
    [x,y,z], [x+sx,y,z], [x+sx,y+sy,z], [x,y+sy,z],
    [x,y,z+sz], [x+sx,y,z+sz], [x+sx,y+sy,z+sz], [x,y+sy,z+sz]
    ]
    faces = []
    faces.append(g.entities.add_face(pts[0],pts[1],pts[2],pts[3]))
    faces.append(g.entities.add_face(pts[4],pts[7],pts[6],pts[5]))
    faces.append(g.entities.add_face(pts[0],pts[4],pts[5],pts[1]))
    faces.append(g.entities.add_face(pts[1],pts[5],pts[6],pts[2]))
    faces.append(g.entities.add_face(pts[2],pts[6],pts[7],pts[3]))
    faces.append(g.entities.add_face(pts[3],pts[7],pts[4],pts[0]))
    for f in faces:
        f.material = mat
        if mat: f.back_material = mat
    return g
# end (def)

# Wall along X or Y with a single opening. Opening is cut structurally by
# splitting wall into left/right (or lower/upper) segments and a lintel.
def wall_with_opening(entities, name=None, axis=None, x=None, y=None, length=None, thickness=None, height=None, opening_offset=None, opening_width=None, opening_height=None, sill=0.0, material=None, layer=None, *extra_args):
    g = group(entities, name, layer)
    if axis == 'x':
        # wall spans x..x+length, thickness in +Y
        a = opening_offset
        b = opening_offset + opening_width
        if a > 0: face_box(g.entities, x, y, 0, a, thickness, height, material, 'Wall_Left', layer)
        if length > b: face_box(g.entities, x+b, y, 0, length-b, thickness, height, material, 'Wall_Right', layer)
        if sill > 0:
            face_box(g.entities, x+a, y, 0, opening_width, thickness, sill, material, 'Wall_Sill', layer)
        # end (if)
        if height > opening_height:
            face_box(g.entities, x+a, y, sill+opening_height, opening_width, thickness,
            height-(sill+opening_height), material, 'Wall_Lintel', layer)
        # end (if)
    else:
        # wall spans y..y+length, thickness in +X
        a = opening_offset
        b = opening_offset + opening_width
        if a > 0: face_box(g.entities, x, y, 0, thickness, a, height, material, 'Wall_Start', layer)
        if length > b: face_box(g.entities, x, y+b, 0, thickness, length-b, height, material, 'Wall_End', layer)
        if sill > 0:
            face_box(g.entities, x, y+a, 0, thickness, opening_width, sill, material, 'Wall_Sill', layer)
        # end (if)
        if height > opening_height:
            face_box(g.entities, x, y+a, sill+opening_height, thickness, opening_width,
            height-(sill+opening_height), material, 'Wall_Lintel', layer)
        # end (if)
    # end (if)
    return g
# end (def)

def door(entities, name, x, y, z, width, height, thickness, orientation, frame_mat, leaf_mat, layer_name='A-Doors', *extra_args):
    g = group(entities, name, layer_name)
    # frame jambs + head, with opening already reserved in the wall
    fw = (0.045 * 1.0)
    if orientation == 'front':  # door plane X-Z, thickness along Y
        face_box(g.entities, x, y, z, fw, thickness, height, frame_mat, 'Jamb_L', layer_name)
        face_box(g.entities, x+width-fw, y, z, fw, thickness, height, frame_mat, 'Jamb_R', layer_name)
        face_box(g.entities, x, y, z+height-fw, width, thickness, fw, frame_mat, 'Head', layer_name)
        face_box(g.entities, x+(0.012 * 1.0), y+(0.015 * 1.0), z+(0.02 * 1.0), width-(0.024 * 1.0), (0.035 * 1.0), height-(0.035 * 1.0), leaf_mat, 'Door_Leaf', layer_name)
        face_box(g.entities, x+width-(0.09 * 1.0), y-(0.01 * 1.0), z+(1.0 * 1.0), (0.018 * 1.0), (0.02 * 1.0), (0.025 * 1.0), frame_mat, 'Handle', layer_name)
    else:  # plane Y-Z, thickness along X
        face_box(g.entities, x, y, z, thickness, fw, height, frame_mat, 'Jamb_L', layer_name)
        face_box(g.entities, x, y+width-fw, z, thickness, fw, height, frame_mat, 'Jamb_R', layer_name)
        face_box(g.entities, x, y, z+height-fw, thickness, width, fw, frame_mat, 'Head', layer_name)
        face_box(g.entities, x+(0.015 * 1.0), y+(0.012 * 1.0), z+(0.02 * 1.0), (0.035 * 1.0), width-(0.024 * 1.0), height-(0.035 * 1.0), leaf_mat, 'Door_Leaf', layer_name)
    # end (if)
    return g
# end (def)

def window(entities, name, x, y, z, width, height, thickness, orientation, frame_mat, glass_mat, layer_name='A-Windows', *extra_args):
    g = group(entities, name, layer_name)
    fw = (0.05 * 1.0)
    if orientation == 'front':
        face_box(g.entities, x, y, z, fw, thickness, height, frame_mat, 'Frame_Left', layer_name)
        face_box(g.entities, x+width-fw, y, z, fw, thickness, height, frame_mat, 'Frame_Right', layer_name)
        face_box(g.entities, x, y, z+height-fw, width, thickness, fw, frame_mat, 'Frame_Top', layer_name)
        face_box(g.entities, x, y, z, width, thickness, fw, frame_mat, 'Frame_Bottom', layer_name)
        face_box(g.entities, x+fw, y+thickness*0.2, z+fw, width-2*fw, thickness*0.6, height-2*fw, glass_mat, 'Glazing', layer_name)
        face_box(g.entities, x+width/2-fw/2, y, z+fw, fw, thickness, height-2*fw, frame_mat, 'Mullion', layer_name)
    else:
        face_box(g.entities, x, y, z, thickness, fw, height, frame_mat, 'Frame_Left', layer_name)
        face_box(g.entities, x, y+width-fw, z, thickness, fw, height, frame_mat, 'Frame_Right', layer_name)
        face_box(g.entities, x, y, z+height-fw, thickness, width, fw, frame_mat, 'Frame_Top', layer_name)
        face_box(g.entities, x, y, z, thickness, width, fw, frame_mat, 'Frame_Bottom', layer_name)
        face_box(g.entities, x+thickness*0.2, y+fw, z+fw, thickness*0.6, width-2*fw, height-2*fw, glass_mat, 'Glazing', layer_name)
    # end (if)
    return g
# end (def)

def furniture_box(entities, name, x, y, z, sx, sy, sz, mat, layer='A-Furniture', *extra_args):
    return face_box(entities, x, y, z, sx, sy, sz, mat, name, layer)
# end (def)

def build():
    model = Sketchup.active_model()
    model.start_operation('Create House BIM Model', True)
    if not (model.entities.empty()): model.entities.erase_entities(model.entities.to_a())

    wall_mat = material('Wall - warm white', [232,229,218])
    int_mat  = material('Partition - off white', [220,220,212])
    slab_mat = material('Concrete', [155,155,150])
    roof_mat = material('Roof tile - terracotta', [150,75,52])
    frame_mat = material('Aluminium frame - dark bronze', [65,62,57])
    glass_mat = material('Glass - blue grey', [135,180,195], 0.48)
    door_mat = material('Door leaf - timber', [130,88,55])
    floor_mat = material('Floor tile', [190,185,174])
    furniture_mat = material('Furniture - wood', [150,112,76])
    sanitary_mat = material('Sanitary ware', [245,245,242])
    counter_mat = material('Kitchen counter', [90,91,88])

    # Slab / platform
    face_box(model.entities, 0, 0, -(0.47 * 1.0), W, D, (0.47 * 1.0), slab_mat, 'Foundation_Platform', 'S-Foundation')
    face_box(model.entities, 0, 0, 0, W, D, SLAB_T, floor_mat, 'Floor_Slab', 'S-Floors')

    # Main outer walls. Front is y=0; rear is y=D. Doors/windows are inserted in reserved openings.
    # Front wall split around a 3-panel sliding entry and two windows.
    front = group(model.entities, 'Exterior_Walls_Front', 'A-Walls-Exterior')
    # segments x ranges; wall height 2.8m, thickness 0.2m
    for i, seg in enumerate([[0,0.55],[3.0,0.35],[4.1,0.35],[7.0,0.35],[10.0,1.0]]):
        face_box(front.entities, (seg[0] * 1.0), 0, (0.12 * 1.0), (seg[1] * 1.0), EXT_WALL, WALL_H-(0.12 * 1.0), wall_mat, "Front_Wall_Segment_#{i+1}", 'A-Walls-Exterior')
    # end (loop)
    # Main facade openings: window left, double entry, large right window and side window
    window(model.entities, 'Window_Front_Left', (0.65 * 1.0), -(0.015 * 1.0), (0.95 * 1.0), (1.65 * 1.0), (1.35 * 1.0), (0.07 * 1.0), 'front', frame_mat, glass_mat)
    door(model.entities, 'Door_Front_Sliding_01', (2.05 * 1.0), -(0.02 * 1.0), (0.12 * 1.0), (0.90 * 1.0), (2.15 * 1.0), (0.07 * 1.0), 'front', frame_mat, door_mat)
    door(model.entities, 'Door_Front_Sliding_02', (2.95 * 1.0), -(0.02 * 1.0), (0.12 * 1.0), (0.90 * 1.0), (2.15 * 1.0), (0.07 * 1.0), 'front', frame_mat, door_mat)
    window(model.entities, 'Window_Front_Centre', (4.25 * 1.0), -(0.015 * 1.0), (1.55 * 1.0), (1.55 * 1.0), (0.75 * 1.0), (0.07 * 1.0), 'front', frame_mat, glass_mat)
    door(model.entities, 'Door_Front_Right', (6.65 * 1.0), -(0.02 * 1.0), (0.12 * 1.0), (0.85 * 1.0), (2.15 * 1.0), (0.07 * 1.0), 'front', frame_mat, door_mat)
    window(model.entities, 'Window_Front_Right_Large', (7.65 * 1.0), -(0.015 * 1.0), (0.85 * 1.0), (2.0 * 1.0), (1.45 * 1.0), (0.07 * 1.0), 'front', frame_mat, glass_mat)

    # Rear wall, with high windows
    face_box(model.entities, 0, D-EXT_WALL, (0.12 * 1.0), W, EXT_WALL, WALL_H-(0.12 * 1.0), wall_mat, 'Exterior_Wall_Rear', 'A-Walls-Exterior')
    window(model.entities, 'Window_Rear_Bedroom_3', (1.0 * 1.0), D-(0.03 * 1.0), (1.35 * 1.0), (1.4 * 1.0), (1.0 * 1.0), (0.07 * 1.0), 'front', frame_mat, glass_mat)
    window(model.entities, 'Window_Rear_Bath', (5.0 * 1.0), D-(0.03 * 1.0), (1.8 * 1.0), (0.65 * 1.0), (0.55 * 1.0), (0.07 * 1.0), 'front', frame_mat, glass_mat)
    window(model.entities, 'Window_Rear_Bedroom_2', (8.0 * 1.0), D-(0.03 * 1.0), (1.35 * 1.0), (1.7 * 1.0), (1.0 * 1.0), (0.07 * 1.0), 'front', frame_mat, glass_mat)

    # Left and right side walls (with window openings approximated by segmented walls)
    face_box(model.entities, 0, (0.2 * 1.0), (0.12 * 1.0), EXT_WALL, D-(0.4 * 1.0), WALL_H-(0.12 * 1.0), wall_mat, 'Exterior_Wall_Left', 'A-Walls-Exterior')
    face_box(model.entities, W-EXT_WALL, (0.2 * 1.0), (0.12 * 1.0), EXT_WALL, D-(0.4 * 1.0), WALL_H-(0.12 * 1.0), wall_mat, 'Exterior_Wall_Right', 'A-Walls-Exterior')
    window(model.entities, 'Window_Left_Side', -(0.015 * 1.0), (4.4 * 1.0), (1.35 * 1.0), (1.25 * 1.0), (1.0 * 1.0), (0.07 * 1.0), 'side', frame_mat, glass_mat)
    window(model.entities, 'Window_Right_Side', W-(0.02 * 1.0), (4.4 * 1.0), (1.35 * 1.0), (1.25 * 1.0), (1.0 * 1.0), (0.07 * 1.0), 'side', frame_mat, glass_mat)

    # Internal partitions (layout interpreted from plan; doors are placed at openings)
    # Bedroom 3 (rear left), bath/WC core, bedroom 2 (rear right), bedroom 1 (front right)
    # y positions are measured from front.
    face_box(model.entities, (0.2 * 1.0), (4.45 * 1.0), (0.12 * 1.0), (3.55 * 1.0), INT_WALL, (2.68 * 1.0), int_mat, 'Partition_Bedroom3_Front', 'A-Walls-Interior')
    face_box(model.entities, (0.2 * 1.0), (4.45 * 1.0), (0.12 * 1.0), INT_WALL, (2.55 * 1.0), (2.68 * 1.0), int_mat, 'Partition_Bedroom3_Left', 'A-Walls-Interior')
    face_box(model.entities, (3.65 * 1.0), (4.45 * 1.0), (0.12 * 1.0), INT_WALL, (2.55 * 1.0), (2.68 * 1.0), int_mat, 'Partition_Bedroom3_Right', 'A-Walls-Interior')

    # Bathroom block in the middle rear
    face_box(model.entities, (3.8 * 1.0), (4.45 * 1.0), (0.12 * 1.0), (3.25 * 1.0), INT_WALL, (2.68 * 1.0), int_mat, 'Partition_Bath_Front', 'A-Walls-Interior')
    face_box(model.entities, (3.8 * 1.0), (4.45 * 1.0), (0.12 * 1.0), INT_WALL, (2.55 * 1.0), (2.68 * 1.0), int_mat, 'Partition_Bath_Left', 'A-Walls-Interior')
    face_box(model.entities, (6.95 * 1.0), (4.45 * 1.0), (0.12 * 1.0), INT_WALL, (2.55 * 1.0), (2.68 * 1.0), int_mat, 'Partition_Bath_Right', 'A-Walls-Interior')
    face_box(model.entities, (3.8 * 1.0), (6.95 * 1.0), (0.12 * 1.0), (3.25 * 1.0), INT_WALL, (2.68 * 1.0), int_mat, 'Partition_Bath_Rear', 'A-Walls-Interior')

    # Bedroom 2 rear-right / Bedroom 1 front-right partitions
    face_box(model.entities, (7.05 * 1.0), (4.45 * 1.0), (0.12 * 1.0), (3.75 * 1.0), INT_WALL, (2.68 * 1.0), int_mat, 'Partition_Bedroom2_Front', 'A-Walls-Interior')
    face_box(model.entities, (7.05 * 1.0), (4.45 * 1.0), (0.12 * 1.0), INT_WALL, (2.55 * 1.0), (2.68 * 1.0), int_mat, 'Partition_Bedroom2_Left', 'A-Walls-Interior')
    face_box(model.entities, (10.7 * 1.0), (4.45 * 1.0), (0.12 * 1.0), INT_WALL, (2.55 * 1.0), (2.68 * 1.0), int_mat, 'Partition_Bedroom2_Right', 'A-Walls-Interior')
    face_box(model.entities, (7.05 * 1.0), (2.7 * 1.0), (0.12 * 1.0), (3.65 * 1.0), INT_WALL, (0.1 * 1.0), (2.68 * 1.0), int_mat, 'Partition_Bedroom1_Rear', 'A-Walls-Interior')
    face_box(model.entities, (7.05 * 1.0), (0.2 * 1.0), (0.12 * 1.0), INT_WALL, (2.55 * 1.0), (2.68 * 1.0), int_mat, 'Partition_Bedroom1_Left', 'A-Walls-Interior')

    # Small WC partition and central hallway
    face_box(model.entities, (5.0 * 1.0), (2.9 * 1.0), (0.12 * 1.0), (2.0 * 1.0), INT_WALL, (0.1 * 1.0), (2.25 * 1.0), int_mat, 'Partition_WC_Front', 'A-Walls-Interior')
    face_box(model.entities, (5.0 * 1.0), (2.9 * 1.0), (0.12 * 1.0), INT_WALL, (1.35 * 1.0), (2.25 * 1.0), int_mat, 'Partition_WC_Left', 'A-Walls-Interior')
    face_box(model.entities, (6.9 * 1.0), (2.9 * 1.0), (0.12 * 1.0), INT_WALL, (1.35 * 1.0), (2.25 * 1.0), int_mat, 'Partition_WC_Right', 'A-Walls-Interior')

    # Interior doors; openings are represented by door components, sizes can be edited
    door(model.entities, 'Door_Bedroom3', (3.2 * 1.0), (4.40 * 1.0), (0.12 * 1.0), (0.75 * 1.0), (2.05 * 1.0), (0.06 * 1.0), 'front', frame_mat, door_mat)
    door(model.entities, 'Door_Bath_01', (4.1 * 1.0), (4.40 * 1.0), (0.12 * 1.0), (0.70 * 1.0), (2.05 * 1.0), (0.06 * 1.0), 'front', frame_mat, door_mat)
    door(model.entities, 'Door_Bath_02', (6.15 * 1.0), (4.40 * 1.0), (0.12 * 1.0), (0.70 * 1.0), (2.05 * 1.0), (0.06 * 1.0), 'front', frame_mat, door_mat)
    door(model.entities, 'Door_Bedroom2', (7.2 * 1.0), (4.40 * 1.0), (0.12 * 1.0), (0.75 * 1.0), (2.05 * 1.0), (0.06 * 1.0), 'front', frame_mat, door_mat)
    door(model.entities, 'Door_Bedroom1', (7.25 * 1.0), (2.65 * 1.0), (0.12 * 1.0), (0.80 * 1.0), (2.05 * 1.0), (0.06 * 1.0), 'front', frame_mat, door_mat)
    door(model.entities, 'Door_WC3', (6.15 * 1.0), (2.85 * 1.0), (0.12 * 1.0), (0.65 * 1.0), (2.0 * 1.0), (0.06 * 1.0), 'front', frame_mat, door_mat)

    # Interior furniture - beds, wardrobes, kitchen counters, dining table, sanitary ware
    furniture_box(model.entities, 'Bed_Bedroom3_Base', (0.55 * 1.0), (5.15 * 1.0), (0.12 * 1.0), (1.55 * 1.0), (2.0 * 1.0), (0.28 * 1.0), furniture_mat)
    furniture_box(model.entities, 'Bed_Bedroom3_Mattress', (0.58 * 1.0), (5.18 * 1.0), (0.40 * 1.0), (1.49 * 1.0), (1.94 * 1.0), (0.12 * 1.0), sanitary_mat)
    furniture_box(model.entities, 'Wardrobe_Bedroom3', (2.45 * 1.0), (5.15 * 1.0), (0.12 * 1.0), (0.55 * 1.0), (1.4 * 1.0), (2.1 * 1.0), furniture_mat)
    furniture_box(model.entities, 'Bed_Bedroom2_Base', (8.25 * 1.0), (5.0 * 1.0), (0.12 * 1.0), (1.65 * 1.0), (2.0 * 1.0), (0.28 * 1.0), furniture_mat)
    furniture_box(model.entities, 'Bed_Bedroom2_Mattress', (8.28 * 1.0), (5.03 * 1.0), (0.40 * 1.0), (1.59 * 1.0), (1.94 * 1.0), (0.12 * 1.0), sanitary_mat)
    furniture_box(model.entities, 'Wardrobe_Bedroom2', (9.95 * 1.0), (4.65 * 1.0), (0.12 * 1.0), (0.55 * 1.0), (1.5 * 1.0), (2.1 * 1.0), furniture_mat)
    furniture_box(model.entities, 'Bed_Bedroom1_Base', (8.2 * 1.0), (0.55 * 1.0), (0.12 * 1.0), (1.65 * 1.0), (2.0 * 1.0), (0.28 * 1.0), furniture_mat)
    furniture_box(model.entities, 'Bed_Bedroom1_Mattress', (8.23 * 1.0), (0.58 * 1.0), (0.40 * 1.0), (1.59 * 1.0), (1.94 * 1.0), (0.12 * 1.0), sanitary_mat)
    furniture_box(model.entities, 'Wardrobe_Bedroom1', (7.25 * 1.0), (0.55 * 1.0), (0.12 * 1.0), (0.55 * 1.0), (1.45 * 1.0), (2.1 * 1.0), furniture_mat)

    # Kitchen counters along left/front zone
    furniture_box(model.entities, 'Kitchen_Counter_01', (0.35 * 1.0), (3.2 * 1.0), (0.12 * 1.0), (2.5 * 1.0), (0.62 * 1.0), (0.88 * 1.0), counter_mat)
    furniture_box(model.entities, 'Kitchen_Counter_02', (0.35 * 1.0), (3.85 * 1.0), (0.12 * 1.0), (1.45 * 1.0), (0.62 * 1.0), (0.88 * 1.0), counter_mat)
    furniture_box(model.entities, 'Dining_Table', (1.1 * 1.0), (1.65 * 1.0), (0.78 * 1.0), (2.0 * 1.0), (0.9 * 1.0), (0.08 * 1.0), furniture_mat)
    for i in range(3):
        furniture_box(model.entities, "Dining_Chair_Left_#{i+1}", (0.65 * 1.0)+i*(0.72 * 1.0), (1.35 * 1.0), (0.12 * 1.0), (0.42 * 1.0), (0.42 * 1.0), (0.45 * 1.0), furniture_mat)
        furniture_box(model.entities, "Dining_Chair_Right_#{i+1}", (0.65 * 1.0)+i*(0.72 * 1.0), (2.55 * 1.0), (0.12 * 1.0), (0.42 * 1.0), (0.42 * 1.0), (0.45 * 1.0), furniture_mat)
    # end (loop)

    # WC / bathroom fixtures
    furniture_box(model.entities, 'WC1_Toilet', (4.25 * 1.0), (5.55 * 1.0), (0.12 * 1.0), (0.38 * 1.0), (0.62 * 1.0), (0.42 * 1.0), sanitary_mat, 'A-Fixtures')
    furniture_box(model.entities, 'WC1_Vanity', (4.05 * 1.0), (4.75 * 1.0), (0.12 * 1.0), (0.65 * 1.0), (0.38 * 1.0), (0.82 * 1.0), sanitary_mat, 'A-Fixtures')
    furniture_box(model.entities, 'WC2_Toilet', (6.05 * 1.0), (5.55 * 1.0), (0.12 * 1.0), (0.38 * 1.0), (0.62 * 1.0), (0.42 * 1.0), sanitary_mat, 'A-Fixtures')
    furniture_box(model.entities, 'WC2_Vanity', (6.1 * 1.0), (4.75 * 1.0), (0.12 * 1.0), (0.62 * 1.0), (0.38 * 1.0), (0.82 * 1.0), sanitary_mat, 'A-Fixtures')
    furniture_box(model.entities, 'WC3_Toilet', (6.25 * 1.0), (3.25 * 1.0), (0.12 * 1.0), (0.38 * 1.0), (0.62 * 1.0), (0.42 * 1.0), sanitary_mat, 'A-Fixtures')
    furniture_box(model.entities, 'WC3_Vanity', (5.2 * 1.0), (3.15 * 1.0), (0.12 * 1.0), (0.55 * 1.0), (0.35 * 1.0), (0.82 * 1.0), sanitary_mat, 'A-Fixtures')

    # Front porch / veranda and step
    face_box(model.entities, -(1.5 * 1.0), -(1.2 * 1.0), -(0.12 * 1.0), W+(3.0 * 1.0), (1.2 * 1.0), (0.12 * 1.0), slab_mat, 'Front_Veranda', 'A-Site')
    face_box(model.entities, (0.0 * 1.0), -(1.55 * 1.0), -(0.24 * 1.0), W, (0.35 * 1.0), (0.12 * 1.0), slab_mat, 'Front_Step', 'A-Site')
    # Side/rear veranda strips
    face_box(model.entities, -(1.5 * 1.0), 0, -(0.12 * 1.0), (1.5 * 1.0), D, (0.12 * 1.0), slab_mat, 'Left_Veranda', 'A-Site')
    face_box(model.entities, W, 0, -(0.12 * 1.0), (1.5 * 1.0), D, (0.12 * 1.0), slab_mat, 'Right_Veranda', 'A-Site')

    # Roof: hip roof represented as four sloped planar faces plus fascia.
    # Roof footprint about 14 x 9.6m; ridge runs along X and is shorter than eaves.
    roof = group(model.entities, 'Roof_Hip_Tiled', 'A-Roof')
    x0 = -ROOF_OVERHANG_X
    x1 = W + ROOF_OVERHANG_X
    y0 = -ROOF_OVERHANG_Y
    y1 = D + ROOF_OVERHANG_Y
    z_eave = EAVE_Z
    z_ridge = RIDGE_Z
    ridge_y0 = D*0.35
    ridge_y1 = D*0.65
    p_front_l = Point3d(x0,y0,z_eave)
    p_front_r = Point3d(x1,y0,z_eave)
    p_back_l  = Point3d(x0,y1,z_eave)
    p_back_r  = Point3d(x1,y1,z_eave)
    p_ridge_l = Point3d(0,ridge_y0,z_ridge)
    p_ridge_r = Point3d(W,ridge_y0,z_ridge)
    p_ridge_l2 = Point3d(0,ridge_y1,z_ridge)
    p_ridge_r2 = Point3d(W,ridge_y1,z_ridge)
    for pts in [[p_front_l,p_front_r,p_ridge_r,p_ridge_l], [p_back_l,p_ridge_l2,p_ridge_r2,p_back_r], [p_front_l,p_ridge_l,p_ridge_l2,p_back_l], [p_front_r,p_back_r,p_ridge_r2,p_ridge_r]]:
        f = roof.entities.add_face(pts)
        f.material = roof_mat
        f.back_material = roof_mat
        if f.normal.z < 0: f.reverse_bang()
    # end (loop)
    # Ridge cap and eave fascia bars
    face_box(roof.entities, 0, ridge_y0, z_ridge, W, ridge_y1-ridge_y0, (0.08 * 1.0), roof_mat, 'Roof_Ridge_Cap', 'A-Roof')
    face_box(roof.entities, x0, y0, z_eave-(0.08 * 1.0), x1-x0, (0.08 * 1.0), (0.16 * 1.0), roof_mat, 'Fascia_Front', 'A-Roof')
    face_box(roof.entities, x0, y1-(0.08 * 1.0), z_eave-(0.08 * 1.0), x1-x0, (0.08 * 1.0), (0.16 * 1.0), roof_mat, 'Fascia_Rear', 'A-Roof')

    # Metadata dictionaries make the groups easier to classify for BIM workflows.
    for g in model.entities.grep(Group):
        if not (g.get_attribute('BIM', 'ifc_type')): g.set_attribute('BIM', 'ifc_type', 'IfcBuildingElementProxy')
        g.set_attribute('BIM', 'source', 'Architectural plan - approximate interpretation')
    # end (loop)
    model.set_attribute('BIM', 'project_name', 'Single-storey house - conceptual BIM')
    model.set_attribute('BIM', 'units', 'meters')
    model.commit_operation()
    model.active_view.zoom_extents()
    UI.messagebox("Đã dựng mô hình nhà sơ bộ. Các nhóm cấu kiện đã được gán Tag và metadata BIM.\nKiểm tra lại kích thước/vị trí cửa, tường và mái trước khi dùng cho hồ sơ kỹ thuật.")
    # rescue => e
    # model.abort_operation if model
    # UI.messagebox("Lỗi khi dựng mô hình: #{e.message}\n#{e.backtrace.first}")
    # raise
# end (def rescue)
# end (module/top)

HouseBIMModel.build()