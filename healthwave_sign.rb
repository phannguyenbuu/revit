# frozen_string_literal: true
# SketchUp Ruby - HealthWave wall sign
# Creates an editable 3D approximation of the supplied reference image.
# Run in SketchUp Ruby Console:
# load "C:/path/to/healthwave_sign.rb"
#
# Then choose Plugins > Create HealthWave Sign

module HealthWaveSign
  extend self

  def material(model, name, rgb, alpha = 1.0)
    m = model.materials[name] || model.materials.add(name)
    m.color = rgb
    m.alpha = alpha
    m
  end

  def box(entities, x, y, z, w, d, h, mat = nil)
    pts = [
      [x, y, z], [x+w, y, z],
      [x+w, y+d, z], [x, y+d, z]
    ]
    face = entities.add_face(pts)
    face.pushpull(h)
    face.material = mat if mat
    face.back_material = mat if mat
    face
  end

  def cylinder(entities, center, axis, radius, height, mat, segments = 32)
    edges = entities.add_cylinder(center, axis, radius, height, segments)
    edges.each { |e| e.material = mat if e.respond_to?(:material=) }
    edges
  end

  def text(entities, string, point, height, font, mat, opts = {})
    entities.add_3d_text(
      string,
      opts[:align] || TextAlignCenter,
      font,
      false,             # bold
      false,             # italic
      height,
      0.004.m,
      0.0,
      true,              # filled
      mat
    )
    # add_3d_text creates geometry at origin; move the newest entities.
    group = entities.add_group
    group.name = "Text_#{string.gsub(/\s+/, '_')}"
    group
  end

  def create_text_group(parent, string, x, y, z, height, mat, name)
    g = parent.add_group
    g.name = name
    g.entities.add_3d_text(
      string,
      TextAlignCenter,
      "Arial",
      false,
      false,
      height,
      0.002.m,
      0.0,
      true,
      mat
    )
    # Geometry generated around local origin. Scale/position remains editable.
    bb = g.bounds
    dx = x - (bb.min.x + bb.max.x) / 2.0
    dy = y - (bb.min.y + bb.max.y) / 2.0
    dz = z - bb.min.z
    g.transform!(Geom::Transformation.translation([dx, dy, dz]))
    g
  end

  def build
    model = Sketchup.active_model
    model.start_operation("HealthWave Wall Sign", true)

    model.entities.clear!

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
    sign_w = 1.20.m
    sign_h = 0.72.m
    sign_d = 0.018.m
    sign_x = -sign_w / 2
    sign_y = -0.02.m
    sign_z = 1.15.m

    # Wall panel behind sign
    box(e, -1.55.m, 0, 0, 3.10.m, 0.12.m, 2.65.m, wall)

    # Decorative wall moulding visible in reference
    trim = 0.018.m
    box(e, -1.50.m, -0.008.m, 0.18.m, 2.90.m, 0.02.m, trim, wall_trim)
    box(e, -1.50.m, -0.008.m, 2.43.m, 2.90.m, 0.02.m, trim, wall_trim)
    box(e, -1.50.m, -0.008.m, 0.18.m, trim, 0.02.m, 2.25.m, wall_trim)
    box(e,  1.48.m, -0.008.m, 0.18.m, trim, 0.02.m, 2.25.m, wall_trim)

    # Sign shadow/backplate
    box(e, sign_x - 0.012.m, sign_y + 0.005.m, sign_z - 0.012.m,
        sign_w + 0.024.m, 0.012.m, sign_h + 0.024.m, shadow)

    # White acrylic sign board
    sign_group = e.add_group
    sign_group.name = "HealthWave_Acrylic_Sign"

    box(sign_group.entities, sign_x, sign_y, sign_z,
        sign_w, sign_d, sign_h, acrylic)

    # Thin metallic edge
    edge_t = 0.008.m
    box(sign_group.entities, sign_x, sign_y - edge_t, sign_z,
        sign_w, edge_t, edge_t, edge)
    box(sign_group.entities, sign_x, sign_y - edge_t, sign_z + sign_h - edge_t,
        sign_w, edge_t, edge_t, edge)

    # Four stainless mounting caps
    screw_r = 0.026.m
    screw_h = 0.035.m
    [
      [sign_x + 0.075.m, sign_z + sign_h - 0.075.m],
      [sign_x + sign_w - 0.075.m, sign_z + sign_h - 0.075.m],
      [sign_x + 0.075.m, sign_z + 0.075.m],
      [sign_x + sign_w - 0.075.m, sign_z + 0.075.m]
    ].each_with_index do |(xx, zz), i|
      cylinder(sign_group.entities, [xx, sign_y - screw_h, zz],
               [0, 1, 0], screw_r, screw_h, steel, 32)
      cylinder(sign_group.entities, [xx, sign_y - screw_h - 0.006.m, zz],
               [0, 1, 0], screw_r * 0.72, 0.008.m, steel, 32)
    end

    # Logo: stylized circular green/orange mark.
    # Built as thick arcs and leaf shapes, keeping the recognizable composition.
    logo = sign_group.entities.add_group
    logo.name = "HealthWave_Logo"

    cx = sign_x + sign_w / 2
    cy = sign_y - 0.012.m
    cz = sign_z + sign_h * 0.69
    r_outer = 0.135.m
    r_inner = 0.108.m

    # Arc helper: creates segmented tube-like strips on the sign face.
    arc_group = logo.entities.add_group
    segments = 32

    # Orange lower/left arc
    pts = []
    0.upto(segments) do |i|
      a = 145.degrees + i * (210.degrees / segments)
      pts << [cx + r_outer*Math.cos(a), cy, cz + r_outer*Math.sin(a)]
    end
    pts.each_cons(2) do |p1, p2|
      dx = p2[0]-p1[0]
      dz = p2[2]-p1[2]
      len = Math.sqrt(dx*dx + dz*dz)
      mid = [(p1[0]+p2[0])/2, cy-0.004.m, (p1[2]+p2[2])/2]
      # small rectangular segment
      w = 0.022.m
      box(arc_group.entities, mid[0]-w/2, mid[1], mid[2]-w/2, w, 0.012.m, w, orange)
    end

    # Green upper/right arc
    arc_group2 = logo.entities.add_group
    pts = []
    0.upto(segments) do |i|
      a = -35.degrees + i * (210.degrees / segments)
      pts << [cx + r_outer*Math.cos(a), cy-0.005.m, cz + r_outer*Math.sin(a)]
    end
    pts.each_cons(2) do |p1, p2|
      mid = [(p1[0]+p2[0])/2, cy-0.008.m, (p1[2]+p2[2])/2]
      w = 0.020.m
      box(arc_group2.entities, mid[0]-w/2, mid[1], mid[2]-w/2, w, 0.012.m, w, green)
    end

    # Green/lime leaves
    leaf1 = box(logo.entities, cx-0.045.m, cy-0.018.m, cz-0.055.m,
                 0.065.m, 0.014.m, 0.115.m, green)
    leaf1.transform!(Geom::Transformation.rotation([cx, cy, cz], [0,1,0], -25.degrees))

    leaf2 = box(logo.entities, cx+0.005.m, cy-0.020.m, cz-0.085.m,
                 0.060.m, 0.014.m, 0.095.m, lime)
    leaf2.transform!(Geom::Transformation.rotation([cx, cy, cz], [0,1,0], 25.degrees))

    # Orange dot
    cylinder(logo.entities, [cx+0.052.m, cy-0.020.m, cz-0.005.m],
             [0,1,0], 0.020.m, 0.012.m, orange, 24)

    # Main wordmark
    create_text_group(sign_group, "HealthWave",
                      cx, cy-0.012.m, sign_z + 0.245.m,
                      0.085.m, dark_text, "HealthWave_Wordmark")

    # Tagline
    create_text_group(sign_group, "YOUR BUSINESS TAGLINE GOES HERE",
                      cx, cy-0.012.m, sign_z + 0.155.m,
                      0.030.m, dark_text, "HealthWave_Tagline")

    # Move the board slightly toward the viewer for correct layering.
    # The sign faces toward negative Y.
    view = model.active_view
    view.camera = Sketchup::Camera.new(
      [0, -3.20.m, 1.55.m],
      [0, 0, 1.52.m],
      [0, 0, 1]
    )
    view.camera.perspective = true

    model.commit_operation
    UI.messagebox("HealthWave wall sign created.")
  rescue => ex
    model.abort_operation
    UI.messagebox("Error: #{ex.message}\n#{ex.backtrace.first(6).join("\n")}")
  end

  unless file_loaded?(__FILE__)
    UI.menu("Plugins").add_item("Create HealthWave Sign") { build }
    file_loaded(__FILE__)
  end
end
