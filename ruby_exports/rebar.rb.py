# --- Auto-Transpiled from SketchUp Ruby ---
import math
Math = math
model = Sketchup.active_model()
entities = model.entities
materials = model.materials
layers = model.layers

# ============================================================
# DAM BTCT 300x700, DAI 8400 mm
# SKETCHUP RUBY API - MO HINH 3D + BOM REBAR
#
# LUU Y:
# Day la cau hinh MINH HOA de dung hinh.
# Khong thay the tinh toan ket cau va ban ve duoc duyet.
#
# He toa do:
# X = chieu dai dam
# Y = chieu rong dam
# Z = chieu cao dam
# ============================================================

# require 'sketchup.rb'

class _Mod_DamBTCT_Rebar_300x700(RubyModule): pass
DamBTCT_Rebar_300x700 = _Mod_DamBTCT_Rebar_300x700('DamBTCT_Rebar_300x700', globals())

# extend self

# ----------------------------------------------------------
# 1. THONG SO DAM
# ----------------------------------------------------------

BEAM_L = (8400 * 0.001)
BEAM_B = (300 * 0.001)
BEAM_H = (700 * 0.001)

COVER = (25 * 0.001)
FILLET_R = (12.5 * 0.001)

# Thep doc - cau hinh minh hoa
MAIN_BOTTOM_D = (20 * 0.001)
MAIN_TOP_D    = (16 * 0.001)

N_BOTTOM = 3
N_TOP    = 2

# Thep dai - cau hinh minh hoa
STIRRUP_D = (10 * 0.001)

END_ZONE = (1200 * 0.001)
STIRRUP_SPACING_END = (100 * 0.001)
STIRRUP_SPACING_MID = (200 * 0.001)

# Do dai moc minh hoa, do theo tim thanh
HOOK_L = (100 * 0.001)

# So canh tron hinh tru
CYLINDER_SEGMENTS = 12

# ----------------------------------------------------------
# 2. VAT LIEU
# ----------------------------------------------------------

def create_material(name, rgb, alpha = 255, *extra_args):
    materials = Sketchup.active_model().materials
    mat = materials[name]  or  materials.add(name)

    mat.color = Color(
    rgb[0], rgb[1], rgb[2], alpha
    )

    return mat
# end (def)

# ----------------------------------------------------------
# 3. TAO HOP BE TONG BANG add_face + pushpull
# ----------------------------------------------------------

def add_box(entities, x, y, z, w, h, depth, mat, name, *extra_args):
    group = entities.add_group()
    group.name = name

    pts = [
    Point3d(x,      y,      z),
    Point3d(x + w,  y,      z),
    Point3d(x + w,  y + h,  z),
    Point3d(x,      y + h,  z)
    ]

    face = group.entities.add_face(pts)

    if face:
        if face.normal.z < 0: face.reverse_bang()
        face.pushpull(depth)

        for f in group.entities.grep(Face):
            f.material = mat
            f.back_material = mat
        # end (loop)
    # end (if)

    return group
# end (def)

# ----------------------------------------------------------
# 4. TAO THANH THEP TRON GIUA HAI DIEM
#
# Dung add_circle + pushpull theo vector truc thanh.
# ----------------------------------------------------------

def add_round_bar(entities, p1, p2, diameter, mat, name, *extra_args):
    vector = p2 - p1
    length = vector.length()

    if length < (0.001 * 0.001): return None

    group = entities.add_group()
    group.name = name

    normal = vector.clone()
    normal.normalize_bang()

    circle = group.entities.add_circle(
    p1,
    normal,
    diameter / 2.0,
    CYLINDER_SEGMENTS
    )

    face = group.entities.add_face(circle)

    if face:
        # Dam bao mat co phap tuyen cung chieu truc thanh
        if face.normal.dot(normal) < 0: face.reverse_bang()
        face.pushpull(length)

        for f in group.entities.grep(Face):
            f.material = mat
            f.back_material = mat
        # end (loop)
    # end (if)

    return group
# end (def)

# ----------------------------------------------------------
# 5. TAO THEP DOC
# ----------------------------------------------------------

def add_longitudinal_bar(parent, x1, x2, y, z, diameter, mat, name, *extra_args):

    p1 = Point3d(x1, y, z)
    p2 = Point3d(x2, y, z)

    add_round_bar(
    parent.entities,
    p1, p2,
    diameter,
    mat,
    name
    )
# end (def)

# ----------------------------------------------------------
# 5b. TAO GOC UON CONG FILLET (CUA THEP CHU)
# ----------------------------------------------------------

def add_fillet_elbow(entities, xc, y, zc, r_fillet, start_angle, end_angle, diameter, mat, name, *extra_args):
    group = entities.add_group()
    group.name = name
    segments = 8
    for k in range(0, segments):
        a1 = start_angle + (end_angle - start_angle) * (k / segments)
        a2 = start_angle + (end_angle - start_angle) * ((k + 1) / segments)
        p1 = Point3d(xc + r_fillet * Math.cos(a1), y, zc + r_fillet * Math.sin(a1))
        p2 = Point3d(xc + r_fillet * Math.cos(a2), y, zc + r_fillet * Math.sin(a2))
        add_round_bar(group.entities, p1, p2, diameter, mat, "#{name}_seg_#{k}")
    # end (loop)
    return group
# end (def)

# ----------------------------------------------------------
# 6. TAO MOT CANH DAI THEP TRON
# ----------------------------------------------------------

def add_stirrup_segment(entities, p1, p2, mat, name, *extra_args):
    add_round_bar(
    entities,
    p1, p2,
    STIRRUP_D,
    mat,
    name
    )
# end (def)

# ----------------------------------------------------------
# 7. TAO DAI KIN VA HAI DOAN MOC MINH HOA
#
# Kich thuoc theo tim thanh:
# Y: tu COVER + D/2 den B - COVER - D/2
# Z: tu COVER + D/2 den H - COVER - D/2
# ----------------------------------------------------------

def add_stirrup(parent, x, index, mat, *extra_args):

    tie_group = parent.entities.add_group()
    tie_group.name = "Dai D10 - #{index}"

    # Tim dai theo lop bao ve
    y1 = COVER + STIRRUP_D / 2.0
    y2 = BEAM_B - COVER - STIRRUP_D / 2.0

    z1 = COVER + STIRRUP_D / 2.0
    z2 = BEAM_H - COVER - STIRRUP_D / 2.0

    # Bon dinh dai
    p1 = Point3d(x, y1, z1)
    p2 = Point3d(x, y2, z1)
    p3 = Point3d(x, y2, z2)
    p4 = Point3d(x, y1, z2)

    # Dai kin hinh chu nhat
    add_stirrup_segment(
    tie_group.entities, p1, p2,
    mat, "Dai #{index} - canh duoi"
    )

    add_stirrup_segment(
    tie_group.entities, p2, p3,
    mat, "Dai #{index} - canh phai"
    )

    add_stirrup_segment(
    tie_group.entities, p3, p4,
    mat, "Dai #{index} - canh tren"
    )

    add_stirrup_segment(
    tie_group.entities, p4, p1,
    mat, "Dai #{index} - canh trai"
    )

    # Hai doan moc 100 mm nam CUNG 1 BEN - TAT CA O BEN TRAI theo yeu cau nguoi dung
    dx1 = -STIRRUP_D * 0.45
    dx2 =  STIRRUP_D * 0.45

    # Cung nam o goc tren ben trai (y1, z2) cho tat ca cac dai
    h_start1 = Point3d(x + dx1, y1, z2)
    h_end1   = Point3d(x + dx1, y1 + HOOK_L * 0.707, z2 - HOOK_L * 0.707)

    h_start2 = Point3d(x + dx2, y1, z2)
    h_end2   = Point3d(x + dx2, y1 + HOOK_L * 0.707, z2 - HOOK_L * 0.707)

    add_stirrup_segment(
    tie_group.entities,
    h_start1, h_end1,
    mat, "Dai #{index} - moc 1"
    )

    add_stirrup_segment(
    tie_group.entities,
    h_start2, h_end2,
    mat, "Dai #{index} - moc 2"
    )

    return tie_group
# end (def)

# ----------------------------------------------------------
# 8. TAO DANH SACH VI TRI DAI
#
# Khoang dau: 100 mm
# Khoang giua: 200 mm
# Khoang cuoi: 100 mm
#
# Cac vi tri duoc tinh tu x = COVER + D/2.
# ----------------------------------------------------------

def generate_stirrup_positions():
    positions = []

    x_start = COVER + STIRRUP_D / 2.0
    x_end   = BEAM_L - COVER - STIRRUP_D / 2.0

    x = x_start

    while x <= x_end:
        positions.append(x)

        # Vung gan goi, tinh theo vi tri doc truc dam
        if x < END_ZONE  or  x > (BEAM_L - END_ZONE):
            step = STIRRUP_SPACING_END
        else:
            step = STIRRUP_SPACING_MID
        # end (if)

        x += step
    # end (while)

    return positions
# end (def)

# ----------------------------------------------------------
# 9. TINH KHOI LUONG THEP
# kg/m = d^2 / 162
# d tinh bang mm
# ----------------------------------------------------------

def unit_mass_kg_per_m(diameter_mm, *extra_args):
    return diameter_mm * diameter_mm / 162.0
# end (def)

def kg_from_length(diameter_mm, length_mm, *extra_args):
    length_m = length_mm / 1000.0
    return length_m * unit_mass_kg_per_m(diameter_mm)
# end (def)

# ----------------------------------------------------------
# 10. IN BOM / BBS RA RUBY CONSOLE
# ----------------------------------------------------------

def print_bom(stirrup_count, longitudinal_length_mm, stirrup_length_mm, *extra_args):

    bottom_length = longitudinal_length_mm * N_BOTTOM
    top_length = longitudinal_length_mm * N_TOP

    bottom_mass = kg_from_length(
    (MAIN_BOTTOM_D * 1000.0),
    (bottom_length * 1000.0)
    )

    top_mass = kg_from_length(
    (MAIN_TOP_D * 1000.0),
    (top_length * 1000.0)
    )

    tie_total_length = stirrup_length_mm * stirrup_count

    tie_mass = kg_from_length(
    (STIRRUP_D * 1000.0),
    (tie_total_length * 1000.0)
    )

    print('')
    print('======================================================')
    print('BOM THEP DAM BTCT 300x700 - L = 8400 mm')
    print('CAU HINH MINH HOA - CAN KIEM TRA TINH TOAN')
    print('======================================================')

    print('')
    print('THEP DOC')
    print('------------------------------------------------------')
    print("Thep duoi=#{N_BOTTOM}D20")
    print("  Chieu dai moi thanh=#{(longitudinal_length_mm * 1000.0).round(0)} mm")
    print("  Tong chieu dai=#{((bottom_length * 1000.0) / 1000.0).round(3)} m")
    print("  Khoi luong ly thuyet=#{bottom_mass.round(2)} kg")

    print('')
    print("Thep tren=#{N_TOP}D16")
    print("  Chieu dai moi thanh=#{(longitudinal_length_mm * 1000.0).round(0)} mm")
    print("  Tong chieu dai=#{((top_length * 1000.0) / 1000.0).round(3)} m")
    print("  Khoi luong ly thuyet=#{top_mass.round(2)} kg")

    print('')
    print('THEP DAI')
    print('------------------------------------------------------')
    print("Duong kinh=D10")
    print("So dai=#{stirrup_count} cai")
    print("Chieu dai tinh moi dai=#{((stirrup_length_mm * 1000.0) / 1000.0).round(3)} m")
    print("Tong chieu dai=#{((tie_total_length * 1000.0) / 1000.0).round(3)} m")
    print("Khoi luong ly thuyet=#{tie_mass.round(2)} kg")

    total = bottom_mass + top_mass + tie_mass

    print('')
    print('TONG HOP')
    print('------------------------------------------------------')
    print("Tong khoi luong thep ly thuyet=#{total.round(2)} kg")
    print('Chua bao gom hao hut, noi chong, neo bo sung.')
    print('Chua tinh thep cau tao / thep gia cuong bo sung.')
    print('======================================================')
# end (def)

# ----------------------------------------------------------
# 11. DUNG MO HINH CHINH
# ----------------------------------------------------------

def build():
    model = Sketchup.active_model()

    model.start_operation(
    'Dung dam BTCT 300x700 va rebar',
    True
    )

    # begin
    root = model.entities.add_group()
    root.name = 'DAM BTCT 300x700 L8400'

    # Vat lieu
    concrete_mat = create_material(
    'Be tong xam',
    [165, 165, 160],
    100
    )

    steel_long_mat = create_material(
    'Thep doc do',
    [190, 45, 40]
    )

    steel_tie_mat = create_material(
    'Thep dai xanh',
    [40, 100, 220]
    )

    # Cot gối trong suốt 50% (alpha = 128)
    column_mat = create_material(
    'Be tong cot trong suot',
    [150, 160, 175],
    128
    )
    col_w = (400 * 0.001)
    col_h = BEAM_H + (400 * 0.001)
    col_b = max([BEAM_B + (100 * 0.001), (400 * 0.001)])

    add_box(
    root.entities,
    -col_w / 2.0, (0 * 0.001), (0 * 0.001),
    BEAM_L + col_w, BEAM_B, BEAM_H,
    concrete_mat,
    'Be tong dam 300x700x8400'
    )

    add_box(root.entities, -col_w / 2.0, (BEAM_B - col_b) / 2.0, -(200 * 0.001), col_w, col_b, col_h, column_mat, 'Cot trai')
    add_box(root.entities, BEAM_L - col_w / 2.0, (BEAM_B - col_b) / 2.0, -(200 * 0.001), col_w, col_b, col_h, column_mat, 'Cot phai')

    # ------------------------------------------------------
    # B. THEP DOC DUOI (Thanh 5: 3D20 kem moc neo 90 do uon len cot, goc fillet 12.5mm & mo vat be vao trong)
    # Thu ngan moi dau vao 25mm theo yeu cau nguoi dung
    # ------------------------------------------------------

    x1 = -col_w / 2.0 + COVER + STIRRUP_D + MAIN_BOTTOM_D / 2.0
    x2 = BEAM_L + col_w / 2.0 - (COVER + STIRRUP_D + MAIN_BOTTOM_D / 2.0)

    # Mo rong ve moi ben 50mm
    x1_bot = x1 + (50 * 0.001)
    x2_bot = x2 - (50 * 0.001)

    bottom_z = COVER + STIRRUP_D + MAIN_BOTTOM_D / 2.0
    hook_h = min([(250 * 0.001), BEAM_H - COVER * 2 - STIRRUP_D * 2])

    # Bo tri 3 thanh deu theo chieu rong
    bottom_y_positions = [
    COVER + STIRRUP_D + MAIN_BOTTOM_D / 2.0,
    BEAM_B / 2.0,
    BEAM_B - COVER - STIRRUP_D - MAIN_BOTTOM_D / 2.0
    ]

    for i, y in enumerate(bottom_y_positions):
        # Thanh chay suot ngang (tu x1_bot + FILLET_R den x2_bot - FILLET_R)
        add_longitudinal_bar(
        root,
        x1_bot + FILLET_R, x2_bot - FILLET_R,
        y, bottom_z,
        MAIN_BOTTOM_D,
        steel_long_mat,
        "Thep doc duoi D20 - thanh #{i + 1}"
        )
        # Goc fillet R = 25mm ben trai
        add_fillet_elbow(root.entities, x1_bot + FILLET_R, y, bottom_z + FILLET_R, FILLET_R, math.pi, 1.5 * math.pi, MAIN_BOTTOM_D, steel_long_mat, "Fillet duoi trai #{i+1}")
        # Moc neo 90 do uon len ben trai (tai x1_bot)
        add_round_bar(root.entities, Point3d(x1_bot, y, bottom_z + FILLET_R), Point3d(x1_bot, y, bottom_z + hook_h), MAIN_BOTTOM_D, steel_long_mat, "Moc neo trai #{i+1}")
        # Mo vat be vao trong (giam 1/2: 22mm)
        add_round_bar(root.entities, Point3d(x1_bot, y, bottom_z + hook_h), Point3d(x1_bot + (22 * 0.001), y, bottom_z + hook_h - (22 * 0.001)), MAIN_BOTTOM_D, steel_long_mat, "Mo trai #{i+1}")

        # Goc fillet R = 25mm ben phai
        add_fillet_elbow(root.entities, x2_bot - FILLET_R, y, bottom_z + FILLET_R, FILLET_R, 1.5 * math.pi, 2.0 * math.pi, MAIN_BOTTOM_D, steel_long_mat, "Fillet duoi phai #{i+1}")
        # Moc neo 90 do uon len ben phai (tai x2_bot)
        add_round_bar(root.entities, Point3d(x2_bot, y, bottom_z + FILLET_R), Point3d(x2_bot, y, bottom_z + hook_h), MAIN_BOTTOM_D, steel_long_mat, "Moc neo phai #{i+1}")
        # Mo vat be vao trong (giam 1/2: 22mm)
        add_round_bar(root.entities, Point3d(x2_bot, y, bottom_z + hook_h), Point3d(x2_bot - (22 * 0.001), y, bottom_z + hook_h - (22 * 0.001)), MAIN_BOTTOM_D, steel_long_mat, "Mo phai #{i+1}")
    # end (loop)

    # ------------------------------------------------------
    # C. THEP DOC TREN (Thanh 1: 2D16 kem moc neo 90 do cam xuong cot, goc fillet 25mm & mo vat be vao trong)
    # ------------------------------------------------------

    top_x1 = -col_w / 2.0 + COVER + STIRRUP_D + MAIN_TOP_D / 2.0
    top_x2 = BEAM_L + col_w / 2.0 - (COVER + STIRRUP_D + MAIN_TOP_D / 2.0)
    top_z = BEAM_H - COVER - STIRRUP_D - MAIN_TOP_D / 2.0

    top_y_positions = [
    COVER + STIRRUP_D + MAIN_TOP_D / 2.0,
    BEAM_B - COVER - STIRRUP_D - MAIN_TOP_D / 2.0
    ]

    for i, y in enumerate(top_y_positions):
        # Thanh chay suot ngang (tu top_x1 + FILLET_R den top_x2 - FILLET_R)
        add_longitudinal_bar(
        root,
        top_x1 + FILLET_R, top_x2 - FILLET_R,
        y, top_z,
        MAIN_TOP_D,
        steel_long_mat,
        "Thep doc tren D16 - thanh #{i + 1}"
        )
        # Goc fillet ben trai
        add_fillet_elbow(root.entities, top_x1 + FILLET_R, y, top_z - FILLET_R, FILLET_R, math.pi, 0.5 * math.pi, MAIN_TOP_D, steel_long_mat, "Fillet tren trai #{i+1}")
        # Moc neo 90 do cam xuong ben trai
        add_round_bar(root.entities, Point3d(top_x1, y, top_z - hook_h), Point3d(top_x1, y, top_z - FILLET_R), MAIN_TOP_D, steel_long_mat, "Moc tren trai #{i+1}")
        # Mo vat be vao trong (giam 1/2: 22mm)
        add_round_bar(root.entities, Point3d(top_x1, y, top_z - hook_h), Point3d(top_x1 + (22 * 0.001), y, top_z - hook_h + (22 * 0.001)), MAIN_TOP_D, steel_long_mat, "Mo tren trai #{i+1}")

        # Goc fillet ben phai
        add_fillet_elbow(root.entities, top_x2 - FILLET_R, y, top_z - FILLET_R, FILLET_R, 0.5 * math.pi, 0.0, MAIN_TOP_D, steel_long_mat, "Fillet tren phai #{i+1}")
        # Moc neo 90 do cam xuong ben phai
        add_round_bar(root.entities, Point3d(top_x2, y, top_z - hook_h), Point3d(top_x2, y, top_z - FILLET_R), MAIN_TOP_D, steel_long_mat, "Moc tren phai #{i+1}")
        # Mo vat be vao trong (giam 1/2: 22mm)
        add_round_bar(root.entities, Point3d(top_x2, y, top_z - hook_h), Point3d(top_x2 - (22 * 0.001), y, top_z - hook_h + (22 * 0.001)), MAIN_TOP_D, steel_long_mat, "Mo tren phai #{i+1}")
    # end (loop)

    # ------------------------------------------------------
    # D. THEP GIA CUONG GOI TREN (Thanh 2: L/4 voi mo vat 45 do be vao trong giam 1/2: 35mm)
    # ------------------------------------------------------
    l_quarter = BEAM_L * 0.25
    top_supp_y = BEAM_B / 2.0
    # Goi trai
    add_round_bar(root.entities, Point3d(x1 + FILLET_R, top_supp_y, top_z), Point3d(x1 + l_quarter, top_supp_y, top_z), (18 * 0.001), steel_long_mat, "Thep goi trai L/4")
    add_fillet_elbow(root.entities, x1 + FILLET_R, top_supp_y, top_z - FILLET_R, FILLET_R, math.pi, 0.5 * math.pi, (18 * 0.001), steel_long_mat, "Fillet goi trai")
    add_round_bar(root.entities, Point3d(x1, top_supp_y, top_z - hook_h * 0.8), Point3d(x1, top_supp_y, top_z - FILLET_R), (18 * 0.001), steel_long_mat, "Neo goi trai")
    add_round_bar(root.entities, Point3d(x1 + l_quarter, top_supp_y, top_z), Point3d(x1 + l_quarter - (35 * 0.001), top_supp_y, top_z - (35 * 0.001)), (18 * 0.001), steel_long_mat, "Mo vat 45 do goi trai be vao trong")

    # Goi phai
    add_round_bar(root.entities, Point3d(x2 - l_quarter, top_supp_y, top_z), Point3d(x2 - FILLET_R, top_supp_y, top_z), (18 * 0.001), steel_long_mat, "Thep goi phai L/4")
    add_fillet_elbow(root.entities, x2 - FILLET_R, top_supp_y, top_z - FILLET_R, FILLET_R, 0.5 * math.pi, 0.0, (18 * 0.001), steel_long_mat, "Fillet goi phai")
    add_round_bar(root.entities, Point3d(x2, top_supp_y, top_z - hook_h * 0.8), Point3d(x2, top_supp_y, top_z - FILLET_R), (18 * 0.001), steel_long_mat, "Neo goi phai")
    add_round_bar(root.entities, Point3d(x2 - l_quarter, top_supp_y, top_z), Point3d(x2 - l_quarter + (35 * 0.001), top_supp_y, top_z - (35 * 0.001)), (18 * 0.001), steel_long_mat, "Mo vat 45 do goi phai be vao trong")

    # ------------------------------------------------------
    # E. THEP GIA CUONG BUNG DUOI (Thanh 6: L/8 -> 7L/8 voi mo vat 45 do be vao trong giam 1/2: 30mm)
    # ------------------------------------------------------
    bot_supp_z = bottom_z + MAIN_BOTTOM_D + (4 * 0.001)
    x_bot_l = x1 + BEAM_L * 0.15
    x_bot_r = x2 - BEAM_L * 0.15
    add_round_bar(root.entities, Point3d(x_bot_l, top_supp_y, bot_supp_z), Point3d(x_bot_r, top_supp_y, bot_supp_z), (18 * 0.001), steel_long_mat, "Thep bung duoi")
    add_round_bar(root.entities, Point3d(x_bot_l, top_supp_y, bot_supp_z), Point3d(x_bot_l + (30 * 0.001), top_supp_y, bot_supp_z + (30 * 0.001)), (18 * 0.001), steel_long_mat, "Mo vat trai bung be vao trong")
    add_round_bar(root.entities, Point3d(x_bot_r, top_supp_y, bot_supp_z), Point3d(x_bot_r - (30 * 0.001), top_supp_y, bot_supp_z + (30 * 0.001)), (18 * 0.001), steel_long_mat, "Mo vat phai bung be vao trong")

    # ------------------------------------------------------
    # F. THEP GIA SUON DAM (Thanh 7: 2D12 khi H >= 700)
    # ------------------------------------------------------
    if BEAM_H >= (700 * 0.001):
        mid_z = BEAM_H / 2.0
        for si, y in enumerate([COVER + STIRRUP_D + (6 * 0.001), BEAM_B - COVER - STIRRUP_D - (6 * 0.001)]):
            add_round_bar(root.entities, Point3d(x1, y, mid_z), Point3d(x2, y, mid_z), (12 * 0.001), steel_long_mat, "Thep gia suon #{si+1}")
            add_round_bar(root.entities, Point3d(x1, y, mid_z), Point3d(x1 + (60 * 0.001), y, mid_z + (60 * 0.001)), (12 * 0.001), steel_long_mat, "Moc gia trai #{si+1}")
            add_round_bar(root.entities, Point3d(x2, y, mid_z), Point3d(x2 - (60 * 0.001), y, mid_z + (60 * 0.001)), (12 * 0.001), steel_long_mat, "Moc gia phai #{si+1}")
        # end (loop)
    # end (if)

    # ------------------------------------------------------
    # D. THEP DAI
    # ------------------------------------------------------

    stirrup_positions = generate_stirrup_positions()

    for i, x in enumerate(stirrup_positions):
        add_stirrup(
        root,
        x,
        i + 1,
        steel_tie_mat
        )
    # end (loop)

    # ------------------------------------------------------
    # E. CAMERA VA HIEN THI
    # ------------------------------------------------------

    model.selection.clear()
    model.selection.add(root)

    model.active_view.camera.set(
    Point3d(
    BEAM_L * 0.55,
    -BEAM_L * 0.70,
    BEAM_H * 1.20
    ),
    Point3d(
    BEAM_L / 2.0,
    BEAM_B / 2.0,
    BEAM_H / 2.0
    ),
    Vector3d(0, 0, 1)
    )

    model.active_view.zoom_extents()

    model.commit_operation()

    # ------------------------------------------------------
    # F. BOM
    # ------------------------------------------------------

    # Chu vi dai theo tim thanh, chua tru ban kinh uon:
    tie_y = BEAM_B - 2.0 * COVER - STIRRUP_D
    tie_z = BEAM_H - 2.0 * COVER - STIRRUP_D

    tie_length = 2.0 * (tie_y + tie_z) + 2.0 * HOOK_L

    longitudinal_length = x2 - x1

    print_bom(
    len(stirrup_positions),
    longitudinal_length,
    tie_length
    )

    UI.messagebox(
    "Da tao mo hinh dam BTCT 300x700, dai 8400 mm.\n" \
    "Thep doc: 3D20 duoi, 2D16 tren.\n" \
    "So dai D10=#{len(stirrup_positions)}.\n\n" \
    "Luu y: Cau hinh minh hoa, khong phai ban ve ket cau da duyet."
    )

    # rescue => error
    # model.abort_operation

    # puts error.message
    # puts error.backtrace

    # UI.messagebox(
    # "Loi khi tao mo hinh:\n#{error.message}"
    # )
    # end (begin rescue)
# end (def)

# end (module/top)

# ------------------------------------------------------------
# THUC THI
# ------------------------------------------------------------

DamBTCT_Rebar_300x700.build()