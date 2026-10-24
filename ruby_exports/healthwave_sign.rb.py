# --- Auto-Transpiled from SketchUp Ruby ---
import math
Math = math
model = Sketchup.active_model()
entities = model.entities
materials = model.materials
layers = model.layers

# frozen_string_literal: true
# SketchUp Ruby - HealthWave wall sign
# Creates an editable 3D approximation of the supplied reference image.
# Run in SketchUp Ruby Console:
# load "C:/path/to/healthwave_sign.rb"
#
# Then choose Plugins > Create HealthWave Sign

class _Mod_HealthWaveSign(RubyModule): pass
HealthWaveSign = _Mod_HealthWaveSign('HealthWaveSign', globals())
# extend self

def material(model, name, rgb, alpha = 1.0, *extra_args):
    m = model.materials[name]  or  model.materials.add(name)
    m.color = rgb
    m.alpha = alpha
    return m
# end (def)

def box(entities, x, y, z, w, d, h, mat = None, *extra_args):
    pts = [
    [x, y, z], [x+w, y, z],
    [x+w, y+d, z], [x, y+d, z]
    ]
    face = entities.add_face(pts)
    face.pushpull(h)
    if mat: face.material = mat
    if mat: face.back_material = mat
    return face
# end (def)

def cylinder(entities, center, axis, radius, height, mat, segments = 32, *extra_args):
    edges = entities.add_cylinder(center, axis, radius, height, segments)
    for e in edges:
        if hasattr(e, "material"): e.material = mat
    return edges
# end (def)

def text(entities, string, point, height, font, mat, opts = {}, *extra_args):
    entities.add_3d_text(
    string,
    opts['align']  or  TextAlignCenter,
    font,
    False,             # bold
    False,             # italic
    height,
    (0.004 * 1.0),
    0.0,
    True,              # filled
    mat
    )
    # add_3d_text creates geometry at origin; move the newest entities.
    group = entities.add_group()
    group.name = "Text_#{string.gsub(/\s+/, '_')}"
    return group
# end (def)

def create_text_group(parent, string, x, y, z, height, mat, name, *extra_args):
    g = parent.add_group()
    g.name = name
    g.entities.add_3d_text(
    string,
    TextAlignCenter,
    "Arial",
    False,
    False,
    height,
    (0.002 * 1.0),
    0.0,
    True,
    mat
    )
    # Geometry generated around local origin. Scale/position remains editable.
    bb = g.bounds
    dx = x - (bb.min.x + bb.max.x) / 2.0
    dy = y - (bb.min.y + bb.max.y) / 2.0
    dz = z - bb.min.z
    g.transform_bang(Geom.Transformation.translation([dx, dy, dz]))
    return g
# end (def)

def build():
    model = Sketchup.active_model()
    model.start_operation("HealthWave Wall Sign", True)

    model.entities.clear()

    # Materials
    wall       = material(model, "Gray Wall", [150, 150, 150])
    wall_trim  = material(model, "Wall Trim", [180, 180, 180])
    acrylic    = material(model, "White Acrylic", [250, 250, 248])
    edge       = material(model, "Acrylic Edge", [210, 220, 225])
    steel      = material(model, "Brushed Stainless Steel", [170, 175, 178])
    dark_text  = material(model, "HealthWave Text", [18, 55, 47])
    green      = material(model, "Logo Green", [40, 135, 55])
    lime       = material(model, "Logo Lime", [150, 210, 45])
    orange     = material(model, "Logo Orange", [245, 110, 25])
    shadow     = material(model, "Shadow Spacer", [90, 90, 90])

    e = model.entities

    # Coordinate system:
    # X = horizontal, Y = wall depth, Z = vertical.
    # Sign is approximately 1.20 m x 0.72 m.
    sign_w = (1.20 * 1.0)
    sign_h = (0.72 * 1.0)
    sign_d = (0.018 * 1.0)
    sign_x = -sign_w / 2
    sign_y = -(0.02 * 1.0)
    sign_z = (1.15 * 1.0)

    # Wall panel behind sign
    box(e, -(1.55 * 1.0), 0, 0, (3.10 * 1.0), (0.12 * 1.0), (2.65 * 1.0), wall)

    # Decorative wall moulding visible in reference
    trim = (0.018 * 1.0)
    box(e, -(1.50 * 1.0), -(0.008 * 1.0), (0.18 * 1.0), (2.90 * 1.0), (0.02 * 1.0), trim, wall_trim)
    box(e, -(1.50 * 1.0), -(0.008 * 1.0), (2.43 * 1.0), (2.90 * 1.0), (0.02 * 1.0), trim, wall_trim)
    box(e, -(1.50 * 1.0), -(0.008 * 1.0), (0.18 * 1.0), trim, (0.02 * 1.0), (2.25 * 1.0), wall_trim)
    box(e,  (1.48 * 1.0), -(0.008 * 1.0), (0.18 * 1.0), trim, (0.02 * 1.0), (2.25 * 1.0), wall_trim)

    # Sign shadow/backplate
    box(e, sign_x - (0.012 * 1.0), sign_y + (0.005 * 1.0), sign_z - (0.012 * 1.0),
    sign_w + (0.024 * 1.0), (0.012 * 1.0), sign_h + (0.024 * 1.0), shadow)

    # White acrylic sign board
    sign_group = e.add_group()
    sign_group.name = "HealthWave_Acrylic_Sign"

    box(sign_group.entities, sign_x, sign_y, sign_z,
    sign_w, sign_d, sign_h, acrylic)

    # Thin metallic edge
    edge_t = (0.008 * 1.0)
    box(sign_group.entities, sign_x, sign_y - edge_t, sign_z,
    sign_w, edge_t, edge_t, edge)
    box(sign_group.entities, sign_x, sign_y - edge_t, sign_z + sign_h - edge_t,
    sign_w, edge_t, edge_t, edge)

    # Four stainless mounting caps
    screw_r = (0.026 * 1.0)
    screw_h = (0.035 * 1.0)
    for i, (xx, zz) in enumerate([ [sign_x + (0.075 * 1.0), sign_z + sign_h - (0.075 * 1.0)], [sign_x + sign_w - (0.075 * 1.0), sign_z + sign_h - (0.075 * 1.0)], [sign_x + (0.075 * 1.0), sign_z + (0.075 * 1.0)], [sign_x + sign_w - (0.075 * 1.0), sign_z + (0.075 * 1.0)] ]):
        cylinder(sign_group.entities, [xx, sign_y - screw_h, zz],
        [0, 1, 0], screw_r, screw_h, steel, 32)
        cylinder(sign_group.entities, [xx, sign_y - screw_h - (0.006 * 1.0), zz],
        [0, 1, 0], screw_r * 0.72, (0.008 * 1.0), steel, 32)
    # end (loop)

    # Logo: stylized circular green/orange mark.
    # Built as thick arcs and leaf shapes, keeping the recognizable composition.
    logo = sign_group.entities.add_group()
    logo.name = "HealthWave_Logo"

    cx = sign_x + sign_w / 2
    cy = sign_y - (0.012 * 1.0)
    cz = sign_z + sign_h * 0.69
    r_outer = (0.135 * 1.0)
    r_inner = (0.108 * 1.0)

    # Arc helper: creates segmented tube-like strips on the sign face.
    arc_group = logo.entities.add_group()
    segments = 32

    # Orange lower/left arc
    pts = []
    for i in range(0, (segments) + 1):
        a = (145 * math.pi / 180.0) + i * ((210 * math.pi / 180.0) / segments)
        pts.append([cx + r_outer*Math.cos(a), cy, cz + r_outer*Math.sin(a)])
    # end (loop)
    for p1, p2 in zip(pts[:-1], pts[1:]):
        dx = p2[0]-p1[0]
        dz = p2[2]-p1[2]
        len = Math.sqrt(dx*dx + dz*dz)
        mid = [(p1[0]+p2[0])/2, cy-(0.004 * 1.0), (p1[2]+p2[2])/2]
        # small rectangular segment
        w = (0.022 * 1.0)
        box(arc_group.entities, mid[0]-w/2, mid[1], mid[2]-w/2, w, (0.012 * 1.0), w, orange)
    # end (loop)

    # Green upper/right arc
    arc_group2 = logo.entities.add_group()
    pts = []
    for i in range(0, (segments) + 1):
        a = -(35 * math.pi / 180.0) + i * ((210 * math.pi / 180.0) / segments)
        pts.append([cx + r_outer*Math.cos(a), cy-(0.005 * 1.0), cz + r_outer*Math.sin(a)])
    # end (loop)
    for p1, p2 in zip(pts[:-1], pts[1:]):
        mid = [(p1[0]+p2[0])/2, cy-(0.008 * 1.0), (p1[2]+p2[2])/2]
        w = (0.020 * 1.0)
        box(arc_group2.entities, mid[0]-w/2, mid[1], mid[2]-w/2, w, (0.012 * 1.0), w, green)
    # end (loop)

    # Green/lime leaves
    leaf1 = box(logo.entities, cx-(0.045 * 1.0), cy-(0.018 * 1.0), cz-(0.055 * 1.0),
    (0.065 * 1.0), (0.014 * 1.0), (0.115 * 1.0), green)
    leaf1.transform_bang(Geom.Transformation.rotation([cx, cy, cz], [0,1,0], -(25 * math.pi / 180.0)))

    leaf2 = box(logo.entities, cx+(0.005 * 1.0), cy-(0.020 * 1.0), cz-(0.085 * 1.0),
    (0.060 * 1.0), (0.014 * 1.0), (0.095 * 1.0), lime)
    leaf2.transform_bang(Geom.Transformation.rotation([cx, cy, cz], [0,1,0], (25 * math.pi / 180.0)))

    # Orange dot
    cylinder(logo.entities, [cx+(0.052 * 1.0), cy-(0.020 * 1.0), cz-(0.005 * 1.0)],
    [0,1,0], (0.020 * 1.0), (0.012 * 1.0), orange, 24)

    # Main wordmark
    create_text_group(sign_group, "HealthWave",
    cx, cy-(0.012 * 1.0), sign_z + (0.245 * 1.0),
    (0.085 * 1.0), dark_text, "HealthWave_Wordmark")

    # Tagline
    create_text_group(sign_group, "YOUR BUSINESS TAGLINE GOES HERE",
    cx, cy-(0.012 * 1.0), sign_z + (0.155 * 1.0),
    (0.030 * 1.0), dark_text, "HealthWave_Tagline")

    # Move the board slightly toward the viewer for correct layering.
    # The sign faces toward negative Y.
    view = model.active_view
    view.camera = Sketchup.Camera.new(
    [0, -(3.20 * 1.0), (1.55 * 1.0)],
    [0, 0, (1.52 * 1.0)],
    [0, 0, 1]
    )
    view.camera.perspective = True

    model.commit_operation()
    UI.messagebox("HealthWave wall sign created.")
    # rescue => ex
    # model.abort_operation
    # UI.messagebox("Error: #{ex.message}\n#{ex.backtrace.first(6).join("\n")}")
# end (def rescue)

# unless file_loaded?(__FILE__)
# UI.menu("Plugins").add_item("Create HealthWave Sign") { build }
# file_loaded(__FILE__)
# end (module/top)
# end (module/top)