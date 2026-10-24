# --- Auto-Transpiled from SketchUp Ruby ---
import math
Math = math
model = Sketchup.active_model()
entities = model.entities
materials = model.materials
layers = model.layers

# frozen_string_literal: true
# SketchUp Ruby script - Luxury Bedroom based on the supplied render
# Tested conceptually for SketchUp Ruby API.
# Usage: SketchUp > Window > Ruby Console, then load this file:
# load "luxury_bedroom_render.rb"
#
# The script creates an approximate editable 3D model:
# room shell, parquet floor, bed, slatted feature wall, nightstands,
# lamps, ceiling fan, window, door, rug and simple tropical plants.

class _Mod_LuxuryBedroomRender(RubyModule): pass
LuxuryBedroomRender = _Mod_LuxuryBedroomRender('LuxuryBedroomRender', globals())
# extend self

ROOM_W = (6.20 * 1.0)
ROOM_D = (5.80 * 1.0)
ROOM_H = (3.40 * 1.0)
WALL_T = (0.15 * 1.0)

def mat(model, name, color, alpha = 1.0, *extra_args):
    materials = model.materials
    m = materials[name]  or  materials.add(name)
    m.color = color
    m.alpha = alpha
    return m
# end (def)

def box(entities, x, y, z, w, d, h, material = None, *extra_args):
    pts = [
    [x, y, z], [x+w, y, z], [x+w, y+d, z], [x, y+d, z]
    ]
    face = entities.add_face(pts)
    if face.normal.z < 0: face.reverse_bang()
    face.pushpull(h)
    if material: face.material = material
    if material: face.back_material = material
    return face
# end (def)

def cyl(entities, center, radius, height, material = None, segments = 32, *extra_args):
    e = entities.add_cylinder(center, [0,0,1], radius, height, segments)
    for edge in e:
        if material: edge.material = material
    face = next((x for x in e if isinstance(x, Face)), None)
    if face  and  material: face.material = material
    return e
# end (def)

def group_box(parent, x, y, z, w, d, h, material = None, name = None, *extra_args):
    g = parent.add_group()
    if name: g.name = name
    box(g.entities, x, y, z, w, d, h, material)
    return g
# end (def)

def create_parquet(model, entities, wood, *extra_args):
    # Base floor
    box(entities, 0, 0, 0, ROOM_W, ROOM_D, (0.10 * 1.0), wood)

    # Herringbone-like visual strips
    light = mat(model, "Parquet Light", [112, 67, 38])
    dark  = mat(model, "Parquet Dark",  [78, 45, 27])

    plank_w = (0.11 * 1.0)
    plank_l = (0.58 * 1.0)
    y = (0.20 * 1.0)
    row = 0
    while y < ROOM_D - (0.15 * 1.0):
        x = (0.10 * 1.0)
        offset = (0.0 if (row % 2 == 0) else plank_l * 0.5)
        x -= offset
        while x < ROOM_W:
            # alternating direction creates a simple parquet rhythm
            w = plank_l
            d = plank_w
            m = (light if (((row + (x / plank_l).__floor__()) % 2 == 0)) else dark)
            box(entities, x, y, (0.105 * 1.0), w, d, (0.008 * 1.0), m)
            x += plank_l
        # end (while)
        y += plank_w
        row += 1
    # end (while)
# end (def)

def create_walls(model, entities, wall, trim, *extra_args):
    # Back and side walls; front wall is left open for camera/view.
    box(entities, 0, ROOM_D-WALL_T, 0, ROOM_W, WALL_T, ROOM_H, wall)
    box(entities, 0, 0, 0, WALL_T, ROOM_D, ROOM_H, wall)
    box(entities, ROOM_W-WALL_T, 0, 0, WALL_T, ROOM_D, ROOM_H, wall)

    # Dark skirting
    box(entities, 0, ROOM_D-WALL_T-(0.02 * 1.0), (0.10 * 1.0), ROOM_W, (0.03 * 1.0), (0.12 * 1.0), trim)
    box(entities, (0.10 * 1.0), 0, (0.10 * 1.0), (0.03 * 1.0), ROOM_D, (0.12 * 1.0), trim)
    return box(entities, ROOM_W-(0.13 * 1.0), 0, (0.10 * 1.0), (0.03 * 1.0), ROOM_D, (0.12 * 1.0), trim)
# end (def)

def create_feature_wall(model, entities, wood, gold, *extra_args):
    x0 = (1.55 * 1.0)
    w = (3.10 * 1.0)
    y = ROOM_D - (0.22 * 1.0)
    z = (0.45 * 1.0)

    # warm back panel
    box(entities, x0, y, z, w, (0.10 * 1.0), (2.45 * 1.0), wood)

    # vertical slats
    slat_w = (0.045 * 1.0)
    gap = (0.035 * 1.0)
    x = x0 + (0.08 * 1.0)
    while x < x0 + w - (0.08 * 1.0):
        box(entities, x, y-(0.025 * 1.0), z, slat_w, (0.14 * 1.0), (2.55 * 1.0), gold)
        x += slat_w + gap
    # end (while)

    # dark lower headboard
    box(entities, x0, y-(0.08 * 1.0), (0.72 * 1.0), w, (0.18 * 1.0), (0.92 * 1.0), wood)
    # horizontal rail
    box(entities, x0, y-(0.11 * 1.0), (1.38 * 1.0), w, (0.22 * 1.0), (0.13 * 1.0), wood)

    # stylized tree / bamboo metal sculpture
    trunk_x = x0 + w * 0.52
    cyl(entities, [trunk_x, y-(0.18 * 1.0), (1.48 * 1.0)], (0.035 * 1.0), (1.40 * 1.0), gold, 12)
    for dx,dz,_ in [[-0.42,1.95,25],[-0.22,2.25,-18],[0.22,2.02,22],[0.35,2.40,-22]]:
        return cyl(entities, [trunk_x+(dx * 1.0), y-(0.19 * 1.0), (dz * 1.0)], (0.018 * 1.0), (0.40 * 1.0), gold, 10)
    # end (loop)
# end (def)

def create_bed(model, entities, fabric, wood, dark, *extra_args):
    cx = ROOM_W / 2.0
    bed_w = (2.15 * 1.0)
    bed_d = (2.15 * 1.0)
    x = cx - bed_w/2
    y = (2.30 * 1.0)

    # platform
    box(entities, x-(0.05 * 1.0), y-(0.08 * 1.0), (0.28 * 1.0), bed_w+(0.10 * 1.0), bed_d+(0.12 * 1.0), (0.28 * 1.0), dark)

    # mattress
    box(entities, x, y, (0.56 * 1.0), bed_w, bed_d, (0.30 * 1.0), fabric)

    # duvet
    box(entities, x+(0.02 * 1.0), y+(0.05 * 1.0), (0.86 * 1.0), bed_w-(0.04 * 1.0), bed_d-(0.10 * 1.0), (0.12 * 1.0), fabric)

    # pillows
    for i in range(4):
        px = x + (0.22 * 1.0) + (i % 2) * (0.76 * 1.0)
        py = y + bed_d - (0.48 * 1.0) - (i / 2) * (0.25 * 1.0)
        box(entities, px, py, (0.99 * 1.0), (0.62 * 1.0), (0.38 * 1.0), (0.10 * 1.0), fabric)
    # end (loop)

    # runner
    runner = mat(model, "Bed Runner", [101, 67, 39])
    return box(entities, x+(0.05 * 1.0), y+(0.42 * 1.0), (0.99 * 1.0), bed_w-(0.10 * 1.0), (0.42 * 1.0), (0.025 * 1.0), runner)
# end (def)

def create_nightstand(model, entities, x, y, white, dark, *extra_args):
    box(entities, x, y, (0.62 * 1.0), (0.58 * 1.0), (0.48 * 1.0), (0.48 * 1.0), white)
    return box(entities, x, y, (1.10 * 1.0), (0.58 * 1.0), (0.48 * 1.0), (0.035 * 1.0), dark)
# end (def)

def create_lamp(model, entities, x, y, metal, shade, *extra_args):
    cyl(entities, [x+(0.29 * 1.0), y+(0.24 * 1.0), (1.12 * 1.0)], (0.035 * 1.0), (0.38 * 1.0), metal, 20)
    return cyl(entities, [x+(0.29 * 1.0), y+(0.24 * 1.0), (1.48 * 1.0)], (0.17 * 1.0), (0.18 * 1.0), shade, 32)
# end (def)

def create_plant(model, entities, x, y, pot, leaf, *extra_args):
    cyl(entities, [x+(0.22 * 1.0), y+(0.22 * 1.0), (0.18 * 1.0)], (0.19 * 1.0), (0.34 * 1.0), pot, 24)
    base_z = (0.52 * 1.0)
    for i in range(9):
        a = i * math.pi * 2 / 9.0
        dx = Math.cos(a) * (0.10 * 1.0)
        dy = Math.sin(a) * (0.10 * 1.0)
        # tapered-looking stem
        cyl(entities, [x+(0.22 * 1.0), y+(0.22 * 1.0), base_z], (0.012 * 1.0), (0.65 * 1.0) + (i % 3)*(0.12 * 1.0), leaf, 8)
        # leaf represented by a small flat box
        box(entities, x+(0.22 * 1.0)+dx-(0.08 * 1.0), y+(0.22 * 1.0)+dy-(0.025 * 1.0),
        (0.82 * 1.0)+(i%3)*(0.10 * 1.0), (0.16 * 1.0), (0.05 * 1.0), (0.025 * 1.0), leaf)
    # end (loop)
# end (def)

def create_window(model, entities, frame, glass, *extra_args):
    # Left-side window on the side wall
    x = (0.02 * 1.0)
    y = (1.00 * 1.0)
    z = (1.05 * 1.0)
    w = (0.06 * 1.0)
    d = (2.30 * 1.0)
    h = (1.70 * 1.0)

    box(entities, x, y, z, w, d, h, glass)
    # frame rails
    for yy in [y, y+d/2-(0.025 * 1.0), y+d-(0.05 * 1.0)]:
        box(entities, x-(0.025 * 1.0), yy, z, (0.10 * 1.0), (0.05 * 1.0), h, frame)
    # end (loop)
    for zz in [z, z+h/2-(0.025 * 1.0), z+h-(0.05 * 1.0)]:
        return box(entities, x-(0.025 * 1.0), y, zz, (0.10 * 1.0), d, (0.05 * 1.0), frame)
    # end (loop)
# end (def)

def create_door(model, entities, door_mat, handle, *extra_args):
    x = ROOM_W - (0.16 * 1.0)
    y = (1.10 * 1.0)
    z = (0.15 * 1.0)
    box(entities, x, y, z, (0.06 * 1.0), (0.92 * 1.0), (2.05 * 1.0), door_mat)
    return cyl(entities, [x-(0.05 * 1.0), y+(0.18 * 1.0), (1.18 * 1.0)], (0.025 * 1.0), (0.025 * 1.0), handle, 16)
# end (def)

def create_rug(model, entities, rug, *extra_args):
    return box(entities, (1.00 * 1.0), (1.30 * 1.0), (0.125 * 1.0), (4.20 * 1.0), (3.15 * 1.0), (0.025 * 1.0), rug)
# end (def)

def create_ceiling_fan(model, entities, metal, blade, *extra_args):
    cx = ROOM_W/2
    cy = ROOM_D/2
    z = ROOM_H - (0.12 * 1.0)
    cyl(entities, [cx,cy,z], (0.10 * 1.0), (0.12 * 1.0), metal, 24)

    for i in range(5):
        a = i * 2*math.pi/5.0
        bx = cx + Math.cos(a)*(0.45 * 1.0)
        by = cy + Math.sin(a)*(0.45 * 1.0)
        # elongated blade
        return box(entities, bx-(0.42 * 1.0), by-(0.07 * 1.0), z-(0.04 * 1.0), (0.84 * 1.0), (0.14 * 1.0), (0.035 * 1.0), blade)
    # end (loop)
# end (def)

def setup_camera(model, *extra_args):
    eye = [(3.10 * 1.0), -(1.10 * 1.0), (2.05 * 1.0)]
    target = [(3.10 * 1.0), (2.70 * 1.0), (1.35 * 1.0)]
    up = [0,0,1]
    model.active_view.camera = Sketchup.Camera.new(eye, target, up)
    model.active_view.camera.perspective = True
# end (def)

def build():
    model = Sketchup.active_model()
    model.start_operation("Luxury Bedroom Render", True)

    # Clean model
    model.entities.clear()

    wall   = mat(model, "Warm Ivory Wall", [232, 221, 198])
    white  = mat(model, "Warm White", [242, 238, 226])
    wood   = mat(model, "Walnut", [82, 49, 28])
    dark   = mat(model, "Dark Walnut", [45, 29, 20])
    gold   = mat(model, "Brushed Brass", [150, 112, 58])
    fabric = mat(model, "Cream Fabric", [225, 216, 196])
    rug    = mat(model, "Natural Jute Rug", [154, 128, 91])
    frame  = mat(model, "Window Frame", [48, 45, 39])
    glass  = mat(model, "Window Glass", [135, 190, 220], 0.35)
    metal  = mat(model, "Lamp Metal", [75, 62, 48])
    shade  = mat(model, "Lamp Shade", [221, 202, 153])
    pot    = mat(model, "Plant Pot", [92, 78, 62])
    leaf   = mat(model, "Leaf Green", [49, 105, 53])
    handle = mat(model, "Door Handle", [55, 50, 42])

    entities = model.entities

    create_parquet(model, entities, wood)
    create_walls(model, entities, wall, dark)
    create_feature_wall(model, entities, wood, gold)
    create_bed(model, entities, fabric, wood, dark)

    create_nightstand(model, entities, (0.95 * 1.0), (2.45 * 1.0), white, dark)
    create_nightstand(model, entities, (4.67 * 1.0), (2.45 * 1.0), white, dark)

    create_lamp(model, entities, (0.95 * 1.0), (2.45 * 1.0), metal, shade)
    create_lamp(model, entities, (4.67 * 1.0), (2.45 * 1.0), metal, shade)

    create_plant(model, entities, (0.35 * 1.0), (2.15 * 1.0), pot, leaf)
    create_plant(model, entities, (5.20 * 1.0), (2.15 * 1.0), pot, leaf)

    create_window(model, entities, frame, glass)
    create_door(model, entities, white, handle)
    create_rug(model, entities, rug)
    create_ceiling_fan(model, entities, metal, shade)

    # Simple ceiling recess / perimeter light
    ceiling = mat(model, "Ceiling", [246, 242, 229])
    box(entities, 0, 0, ROOM_H, ROOM_W, ROOM_D, (0.06 * 1.0), ceiling)

    # Named groups for easier editing
    for e in model.entities:
        if hasattr(e, "name")  and  e.name.empty(): e.name = "Bedroom_Element"
    # end (loop)

    setup_camera(model)

    model.commit_operation()
    UI.messagebox("Luxury bedroom model created successfully.")
    # rescue => e
    # model.abort_operation
    # UI.messagebox("Ruby script error: #{e.message}\n#{e.backtrace.first(5).join("\n")}")
# end (def rescue)

# unless file_loaded?(__FILE__)
# UI.menu("Plugins").add_item("Create Luxury Bedroom Render") { build }
# file_loaded(__FILE__)
# end (module/top)
# end (module/top)