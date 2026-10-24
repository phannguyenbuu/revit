# frozen_string_literal: true
# SketchUp Ruby script - Luxury Bedroom based on the supplied render
# Tested conceptually for SketchUp Ruby API.
# Usage: SketchUp > Window > Ruby Console, then load this file:
# load "luxury_bedroom_render.rb"
#
# The script creates an approximate editable 3D model:
# room shell, parquet floor, bed, slatted feature wall, nightstands,
# lamps, ceiling fan, window, door, rug and simple tropical plants.

module LuxuryBedroomRender
  extend self

  ROOM_W = 6.20.m
  ROOM_D = 5.80.m
  ROOM_H = 3.40.m
  WALL_T = 0.15.m

  def mat(model, name, color, alpha = 1.0)
    materials = model.materials
    m = materials[name] || materials.add(name)
    m.color = color
    m.alpha = alpha
    m
  end

  def box(entities, x, y, z, w, d, h, material = nil)
    pts = [
      [x, y, z], [x+w, y, z], [x+w, y+d, z], [x, y+d, z]
    ]
    face = entities.add_face(pts)
    face.reverse! if face.normal.z < 0
    face.pushpull(h)
    face.material = material if material
    face.back_material = material if material
    face
  end

  def cyl(entities, center, radius, height, material = nil, segments = 32)
    e = entities.add_cylinder(center, [0,0,1], radius, height, segments)
    e.each { |edge| edge.material = material if material }
    face = e.find { |x| x.is_a?(Sketchup::Face) }
    face.material = material if face && material
    e
  end

  def group_box(parent, x, y, z, w, d, h, material = nil, name = nil)
    g = parent.add_group
    g.name = name if name
    box(g.entities, x, y, z, w, d, h, material)
    g
  end

  def create_parquet(model, entities, wood)
    # Base floor
    box(entities, 0, 0, 0, ROOM_W, ROOM_D, 0.10.m, wood)

    # Herringbone-like visual strips
    light = mat(model, "Parquet Light", [112, 67, 38])
    dark  = mat(model, "Parquet Dark",  [78, 45, 27])

    plank_w = 0.11.m
    plank_l = 0.58.m
    y = 0.20.m
    row = 0
    while y < ROOM_D - 0.15.m
      x = 0.10.m
      offset = (row.even? ? 0.0 : plank_l * 0.5)
      x -= offset
      while x < ROOM_W
        # alternating direction creates a simple parquet rhythm
        w = plank_l
        d = plank_w
        m = ((row + (x / plank_l).floor) % 2 == 0) ? light : dark
        box(entities, x, y, 0.105.m, w, d, 0.008.m, m)
        x += plank_l
      end
      y += plank_w
      row += 1
    end
  end

  def create_walls(model, entities, wall, trim)
    # Back and side walls; front wall is left open for camera/view.
    box(entities, 0, ROOM_D-WALL_T, 0, ROOM_W, WALL_T, ROOM_H, wall)
    box(entities, 0, 0, 0, WALL_T, ROOM_D, ROOM_H, wall)
    box(entities, ROOM_W-WALL_T, 0, 0, WALL_T, ROOM_D, ROOM_H, wall)

    # Dark skirting
    box(entities, 0, ROOM_D-WALL_T-0.02.m, 0.10.m, ROOM_W, 0.03.m, 0.12.m, trim)
    box(entities, 0.10.m, 0, 0.10.m, 0.03.m, ROOM_D, 0.12.m, trim)
    box(entities, ROOM_W-0.13.m, 0, 0.10.m, 0.03.m, ROOM_D, 0.12.m, trim)
  end

  def create_feature_wall(model, entities, wood, gold)
    x0 = 1.55.m
    w = 3.10.m
    y = ROOM_D - 0.22.m
    z = 0.45.m

    # warm back panel
    box(entities, x0, y, z, w, 0.10.m, 2.45.m, wood)

    # vertical slats
    slat_w = 0.045.m
    gap = 0.035.m
    x = x0 + 0.08.m
    while x < x0 + w - 0.08.m
      box(entities, x, y-0.025.m, z, slat_w, 0.14.m, 2.55.m, gold)
      x += slat_w + gap
    end

    # dark lower headboard
    box(entities, x0, y-0.08.m, 0.72.m, w, 0.18.m, 0.92.m, wood)
    # horizontal rail
    box(entities, x0, y-0.11.m, 1.38.m, w, 0.22.m, 0.13.m, wood)

    # stylized tree / bamboo metal sculpture
    trunk_x = x0 + w * 0.52
    cyl(entities, [trunk_x, y-0.18.m, 1.48.m], 0.035.m, 1.40.m, gold, 12)
    [[-0.42,1.95,25],[-0.22,2.25,-18],[0.22,2.02,22],[0.35,2.40,-22]].each do |dx,dz,_|
      cyl(entities, [trunk_x+dx.m, y-0.19.m, dz.m], 0.018.m, 0.40.m, gold, 10)
    end
  end

  def create_bed(model, entities, fabric, wood, dark)
    cx = ROOM_W / 2.0
    bed_w = 2.15.m
    bed_d = 2.15.m
    x = cx - bed_w/2
    y = 2.30.m

    # platform
    box(entities, x-0.05.m, y-0.08.m, 0.28.m, bed_w+0.10.m, bed_d+0.12.m, 0.28.m, dark)

    # mattress
    box(entities, x, y, 0.56.m, bed_w, bed_d, 0.30.m, fabric)

    # duvet
    box(entities, x+0.02.m, y+0.05.m, 0.86.m, bed_w-0.04.m, bed_d-0.10.m, 0.12.m, fabric)

    # pillows
    4.times do |i|
      px = x + 0.22.m + (i % 2) * 0.76.m
      py = y + bed_d - 0.48.m - (i / 2) * 0.25.m
      box(entities, px, py, 0.99.m, 0.62.m, 0.38.m, 0.10.m, fabric)
    end

    # runner
    runner = mat(model, "Bed Runner", [101, 67, 39])
    box(entities, x+0.05.m, y+0.42.m, 0.99.m, bed_w-0.10.m, 0.42.m, 0.025.m, runner)
  end

  def create_nightstand(model, entities, x, y, white, dark)
    box(entities, x, y, 0.62.m, 0.58.m, 0.48.m, 0.48.m, white)
    box(entities, x, y, 1.10.m, 0.58.m, 0.48.m, 0.035.m, dark)
  end

  def create_lamp(model, entities, x, y, metal, shade)
    cyl(entities, [x+0.29.m, y+0.24.m, 1.12.m], 0.035.m, 0.38.m, metal, 20)
    cyl(entities, [x+0.29.m, y+0.24.m, 1.48.m], 0.17.m, 0.18.m, shade, 32)
  end

  def create_plant(model, entities, x, y, pot, leaf)
    cyl(entities, [x+0.22.m, y+0.22.m, 0.18.m], 0.19.m, 0.34.m, pot, 24)
    base_z = 0.52.m
    9.times do |i|
      a = i * Math::PI * 2 / 9.0
      dx = Math.cos(a) * 0.10.m
      dy = Math.sin(a) * 0.10.m
      # tapered-looking stem
      cyl(entities, [x+0.22.m, y+0.22.m, base_z], 0.012.m, 0.65.m + (i % 3)*0.12.m, leaf, 8)
      # leaf represented by a small flat box
      box(entities, x+0.22.m+dx-0.08.m, y+0.22.m+dy-0.025.m,
          0.82.m+(i%3)*0.10.m, 0.16.m, 0.05.m, 0.025.m, leaf)
    end
  end

  def create_window(model, entities, frame, glass)
    # Left-side window on the side wall
    x = 0.02.m
    y = 1.00.m
    z = 1.05.m
    w = 0.06.m
    d = 2.30.m
    h = 1.70.m

    box(entities, x, y, z, w, d, h, glass)
    # frame rails
    [y, y+d/2-0.025.m, y+d-0.05.m].each do |yy|
      box(entities, x-0.025.m, yy, z, 0.10.m, 0.05.m, h, frame)
    end
    [z, z+h/2-0.025.m, z+h-0.05.m].each do |zz|
      box(entities, x-0.025.m, y, zz, 0.10.m, d, 0.05.m, frame)
    end
  end

  def create_door(model, entities, door_mat, handle)
    x = ROOM_W - 0.16.m
    y = 1.10.m
    z = 0.15.m
    box(entities, x, y, z, 0.06.m, 0.92.m, 2.05.m, door_mat)
    cyl(entities, [x-0.05.m, y+0.18.m, 1.18.m], 0.025.m, 0.025.m, handle, 16)
  end

  def create_rug(model, entities, rug)
    box(entities, 1.00.m, 1.30.m, 0.125.m, 4.20.m, 3.15.m, 0.025.m, rug)
  end

  def create_ceiling_fan(model, entities, metal, blade)
    cx = ROOM_W/2
    cy = ROOM_D/2
    z = ROOM_H - 0.12.m
    cyl(entities, [cx,cy,z], 0.10.m, 0.12.m, metal, 24)

    5.times do |i|
      a = i * 2*Math::PI/5.0
      bx = cx + Math.cos(a)*0.45.m
      by = cy + Math.sin(a)*0.45.m
      # elongated blade
      box(entities, bx-0.42.m, by-0.07.m, z-0.04.m, 0.84.m, 0.14.m, 0.035.m, blade)
    end
  end

  def setup_camera(model)
    eye = [3.10.m, -1.10.m, 2.05.m]
    target = [3.10.m, 2.70.m, 1.35.m]
    up = [0,0,1]
    model.active_view.camera = Sketchup::Camera.new(eye, target, up)
    model.active_view.camera.perspective = true
  end

  def build
    model = Sketchup.active_model
    model.start_operation("Luxury Bedroom Render", true)

    # Clean model
    model.entities.clear!

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

    create_nightstand(model, entities, 0.95.m, 2.45.m, white, dark)
    create_nightstand(model, entities, 4.67.m, 2.45.m, white, dark)

    create_lamp(model, entities, 0.95.m, 2.45.m, metal, shade)
    create_lamp(model, entities, 4.67.m, 2.45.m, metal, shade)

    create_plant(model, entities, 0.35.m, 2.15.m, pot, leaf)
    create_plant(model, entities, 5.20.m, 2.15.m, pot, leaf)

    create_window(model, entities, frame, glass)
    create_door(model, entities, white, handle)
    create_rug(model, entities, rug)
    create_ceiling_fan(model, entities, metal, shade)

    # Simple ceiling recess / perimeter light
    ceiling = mat(model, "Ceiling", [246, 242, 229])
    box(entities, 0, 0, ROOM_H, ROOM_W, ROOM_D, 0.06.m, ceiling)

    # Named groups for easier editing
    model.entities.each do |e|
      e.name = "Bedroom_Element" if e.respond_to?(:name) && e.name.to_s.empty?
    end

    setup_camera(model)

    model.commit_operation
    UI.messagebox("Luxury bedroom model created successfully.")
  rescue => e
    model.abort_operation
    UI.messagebox("Ruby script error: #{e.message}\n#{e.backtrace.first(5).join("\n")}")
  end

  unless file_loaded?(__FILE__)
    UI.menu("Plugins").add_item("Create Luxury Bedroom Render") { build }
    file_loaded(__FILE__)
  end
end
