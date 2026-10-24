# Mother of Perpetual Help Catholic Parish — conceptual SketchUp Ruby model
# Units: meters. Run in SketchUp via Window > Ruby Console:
# load "C:/path/to/mother_of_perpetual_help_parish.rb"
#
# This script creates a schematic architectural model based on the supplied
# photographs and aerial view. Dimensions are inferred, not surveyed.
# It does NOT claim to reproduce hidden structure or exact site measurements.

module MotherOfPerpetualHelpParish
  extend self

  def run
    model = Sketchup.active_model
    model.start_operation("Build Mother of Perpetual Help Parish", true)
    model.entities.clear!
    @m = model
    @ents = model.entities
    @materials = {}
    make_materials

    # Ground and forecourt
    box("Site paving", [0, -19, -0.18], [38, 17, 0.18], mat("Concrete"))
    box("Main building plinth", [-14, -2.0, 0], [28, 16, 0.45], mat("Stone"))
    box("Forecourt apron", [-18, -25, -0.08], [36, 7, 0.08], mat("Paving"))

    # Long, low parish wings, behind the tower
    build_wing(-14.0, 0, 13.5, 7.8, "Left wing")
    build_wing(0.5, 0, 13.5, 7.8, "Right wing")

    # Central tower: four massive pale piers around open belfry bays
    build_tower

    # Roofs are modeled as simple pitched hip/gable volumes with tile-colored surfaces.
    build_wing_roof(-14.0, 0, 13.5, 7.8, "Left wing roof")
    build_wing_roof(0.5, 0, 13.5, 7.8, "Right wing roof")

    # Entrance steps and accessible ramp/rails
    box("Entrance landing", [-3.6, -3.6, 0.0], [7.2, 1.8, 0.18], mat("Stone"))
    3.times do |i|
      box("Entry step #{i+1}", [-3.1, -4.0 - i*0.42, -0.10-i*0.10],
          [6.2, 0.48, 0.12], mat("Stone"))
    end
    box("Ramp", [4.2, -5.1, 0.03], [1.15, 3.0, 0.12], mat("Concrete"))
    rail([-0.9,-3.1,0.8],[-0.9,-5.5,0.55])
    rail([0.9,-3.1,0.8],[0.9,-5.5,0.55])

    # Decorative planters
    [[-7,-4],[7,-4],[-11,-2],[11,-2],[-5,-7],[5,-7]].each_with_index do |p,i|
      cylinder("Planter #{i+1}", p[0], p[1], 0.0, 0.42, 0.45, mat("Terracotta"), 20)
      cylinder("Shrub #{i+1}", p[0], p[1], 0.45, 0.52, 0.85, mat("Shrub"), 16)
    end

    # Site/context markers
    box("Roadway", [-20, -32, -0.25], [40, 6.5, 0.12], mat("Road"))
    model.active_view.zoom_extents
    model.commit_operation
  rescue => e
    model.abort_operation rescue nil
    UI.messagebox("Model generation failed:\n#{e.message}\n#{e.backtrace.first}")
  end

  def make_materials
    {
      "Ivory" => [229, 222, 202], "Ivory shadow" => [202, 195, 176],
      "Tile" => [153, 63, 47], "Tile light" => [177, 83, 62],
      "Glass" => [34, 43, 51], "Frame" => [43, 40, 35],
      "Stone" => [190, 183, 164], "Concrete" => [180, 177, 166],
      "Paving" => [151, 148, 138], "Road" => [89, 89, 86],
      "Gold" => [207, 170, 58], "Icon blue" => [49, 82, 133],
      "Icon yellow" => [235, 207, 62], "White" => [245, 240, 220],
      "Terracotta" => [133, 66, 47], "Shrub" => [58, 91, 43],
      "Black" => [28, 28, 26], "Metal" => [92, 92, 86]
    }.each do |name, rgb|
      m = @m.materials.add(name)
      m.color = Sketchup::Color.new(*rgb)
      m.alpha = (name == "Glass" ? 0.78 : 1.0)
      @materials[name] = m
    end
  end

  def mat(name); @materials[name]; end
  def pt(x,y,z); Geom::Point3d.new(x.m, y.m, z.m); end

  def box(name, origin, size, material)
    x,y,z = origin; dx,dy,dz = size
    g = @ents.add_group
    g.name = name
    e = g.entities
    pts = [[x,y,z],[x+dx,y,z],[x+dx,y+dy,z],[x,y+dy,z]].map { |a| pt(*a) }
    f = e.add_face(pts)
    f.reverse! if f.normal.z < 0
    f.pushpull(dz.m)
    g.material = material
    g.entities.each { |en| en.material = material if en.respond_to?(:material=) }
    g
  end

  def cylinder(name, x,y,z, radius,height, material, segments=16)
    g = @ents.add_group; g.name = name
    circle = g.entities.add_circle(pt(x,y,z), Z_AXIS, radius.m, segments)
    face = g.entities.add_face(circle)
    face.pushpull(height.m)
    g.material = material
    g.entities.each { |e| e.material = material if e.respond_to?(:material=) }
    g
  end

  def rail(a,b)
    p1=pt(*a); p2=pt(*b)
    v=p2-p1
    @ents.add_line(p1,p2).material = mat("Metal")
    # vertical supports along the handrail
    5.times do |i|
      t=i/4.0
      x=a[0]+(b[0]-a[0])*t; y=a[1]+(b[1]-a[1])*t; z=a[2]+(b[2]-a[2])*t
      @ents.add_line(pt(x,y,z-0.65),pt(x,y,z)).material = mat("Metal")
    end
  end

  def build_wing(x,y,zbase,length, label)
    # Main wall volume, with front facing toward negative Y
    box("#{label} wall mass", [x,y,zbase*0], [length, 7.8, 5.0], mat("Ivory"))
    # Front wall pilasters and repeated arched window bays
    count = 4
    bay = length.to_f / count
    count.times do |i|
      cx = x + bay*(i+0.5)
      build_arch_window(cx, -0.015, 1.0, 2.35, 2.7, "#{label} arched window #{i+1}")
      box("#{label} pilaster #{i+1}", [x+i*bay, -0.12, 0], [0.22,0.22,5.0], mat("Ivory shadow"))
    end
    # Corner quoins and base course
    box("#{label} base course", [x,-0.16,0], [length,0.18,0.48], mat("Ivory shadow"))
    # Side wall clerestory-like dark opening bands
    box("#{label} rear trim", [x,7.65,4.55], [length,0.18,0.18], mat("Ivory shadow"))
  end

  def build_arch_window(cx, y, z, width, height, label)
    g=@ents.add_group; g.name=label; e=g.entities
    # Dark rectangular glazing field with a segmented semicircular top
    w=width; h=height; r=w/2.0
    # Face lies in X-Z plane; use points at constant y
    outline=[pt(cx-r,y,z),pt(cx+r,y,z),pt(cx+r,y,z+h-r)]
    12.times do |i|
      ang = i*Math::PI/12.0
      outline << pt(cx+r*Math.cos(ang), y, z+h-r+r*Math.sin(ang))
    end
    outline << pt(cx-r,y,z)
    f=e.add_face(outline)
    f.material=mat("Glass"); f.back_material=mat("Glass")
    # Outer arch frame as fine straight segments
    e.add_line(pt(cx-r-0.10,y-0.02,z),pt(cx-r-0.10,y-0.02,z+h-r))
    e.add_line(pt(cx+r+0.10,y-0.02,z),pt(cx+r+0.10,y-0.02,z+h-r))
    e.add_line(pt(cx-r-0.10,y-0.02,z),pt(cx+r+0.10,y-0.02,z))
    12.times do |i|
      a=Math::PI*i/12.0; b=Math::PI*(i+1)/12.0
      e.add_line(pt(cx+r*Math.cos(a),y-0.025,z+h-r+r*Math.sin(a)),
                 pt(cx+r*Math.cos(b),y-0.025,z+h-r+r*Math.sin(b)))
    end
    # Mullions
    e.add_line(pt(cx,y-0.03,z),pt(cx,y-0.03,z+h))
    e.add_line(pt(cx-r,y-0.03,z+1.0),pt(cx+r,y-0.03,z+1.0))
    g
  end

  def build_wing_roof(x,y,length,depth,label)
    # Pitched roof approximated by a set of sloped planar panels, ridge running along X.
    e=@ents.add_group; e.name=label; ents=e.entities
    z0=5.0; ridge=6.55
    # Front slope, rear slope and end caps
    p1=pt(x,y-0.55,z0); p2=pt(x+length,y-0.55,z0)
    p3=pt(x+length,y+depth/2.0,ridge); p4=pt(x,y+depth/2.0,ridge)
    f=ents.add_face(p1,p2,p3,p4); f.material=mat("Tile"); f.back_material=mat("Tile")
    p5=pt(x,y+depth/2.0,ridge); p6=pt(x+length,y+depth/2.0,ridge)
    p7=pt(x+length,y+depth+0.3,z0); p8=pt(x,y+depth+0.3,z0)
    f2=ents.add_face(p5,p6,p7,p8); f2.material=mat("Tile"); f2.back_material=mat("Tile")
    # Roof fascia
    ents.add_line(p1,p2).material=mat("Tile light")
    ents.add_line(p7,p8).material=mat("Tile light")
    # Tile courses, subtle seams
    14.times do |i|
      xx=x+length*i/14.0
      ents.add_line(pt(xx,y-0.52,z0+0.025),pt(xx,y+depth/2.0,ridge+0.025)).material=mat("Tile light")
      ents.add_line(pt(xx,y+depth/2.0,ridge+0.025),pt(xx,y+depth+0.27,z0+0.025)).material=mat("Tile light")
    end
    e
  end

  def build_tower
    # Tower dimensions approximately 7.0m wide x 6.5m deep, height 16.5m
    tw=7.0; td=6.4; x=-3.5; y=-0.2
    # Lower solid tower base with entrance arch opening represented by a dark recessed doorway
    box("Tower lower left pier", [x,y,0], [1.25,td,7.0], mat("Ivory"))
    box("Tower lower right pier", [x+tw-1.25,y,0], [1.25,td,7.0], mat("Ivory"))
    box("Tower rear wall", [x+1.25,y+td-0.45,0], [tw-2.5,0.45,7.0], mat("Ivory"))
    # Entrance dark inset and arch surround
    box("Main entrance dark recess", [-2.05,-0.23,0.35], [4.1,0.12,3.65], mat("Black"))
    build_arch_outline(0,-0.28,0.35,4.25,4.0,"Main entrance arch")
    box("Entrance door glazing", [-1.7,-0.31,0.45], [3.4,0.10,2.65], mat("Glass"))
    4.times do |i|
      xx=-1.7+i*0.85
      @ents.add_line(pt(xx,-0.38,0.5),pt(xx,-0.38,3.05)).material=mat("Frame")
    end
    # Upper tower piers continue up, leaving open belfry openings
    box("Tower upper left pier", [x,y,7.0], [1.35,td,9.2], mat("Ivory"))
    box("Tower upper right pier", [x+tw-1.35,y,7.0], [1.35,td,9.2], mat("Ivory"))
    box("Tower rear upper pier", [x+1.35,y+td-0.4,7.0], [tw-2.7,0.4,9.2], mat("Ivory"))
    # Cross beams / open belfry levels
    box("Belfry lower crossbeam", [-2.15,y+0.2,8.1], [4.3,0.55,0.45], mat("Ivory shadow"))
    box("Belfry upper crossbeam", [-2.15,y+0.2,11.5], [4.3,0.55,0.45], mat("Ivory shadow"))
    box("Icon support ledge", [-2.3,y-0.25,12.3], [4.6,0.85,0.32], mat("Stone"))
    # Marian icon panel, gold frame and simplified colorful inset
    box("Icon gold surround", [-1.55,y-0.36,12.65], [3.1,0.24,3.45], mat("Gold"))
    box("Icon yellow background", [-1.37,y-0.40,12.82], [2.74,0.10,3.1], mat("Icon yellow"))
    box("Icon central image field", [-1.13,y-0.47,13.0], [2.26,0.08,2.72], mat("Icon blue"))
    # stylized halo and robe geometry
    cylinder("Icon halo", 0, y-0.54, 14.65, 0.47, 0.035, mat("Gold"), 32)
    box("Icon robe", [-0.55,y-0.56,13.25], [1.1,0.06,1.25], mat("White"))
    cylinder("Icon head", -0.03, y-0.62, 14.15, 0.24, 0.08, mat("Stone"), 20)
    cylinder("Child halo", 0.45, y-0.65, 13.75, 0.17, 0.04, mat("Gold"), 20)
    cylinder("Child head", 0.45, y-0.68, 13.55, 0.13, 0.07, mat("Stone"), 20)
    # Top cornice and broad upturned red roof
    box("Tower roof soffit", [-4.25,y-1.0,16.2], [8.5,8.4,0.42], mat("Ivory shadow"))
    build_tower_roof
    # Cross above roof
    box("Cross vertical", [-0.12,2.65,18.1], [0.24,0.24,1.55], mat("Black"))
    box("Cross horizontal", [-0.72,2.65,18.95], [1.44,0.24,0.24], mat("Black"))
    # Sign panel over entrance
    box("Parish sign backing", [-2.45,-0.38,5.05], [4.9,0.22,0.62], mat("Gold"))
    # Small red lettering strokes to suggest sign text
    8.times do |i|
      xx=-2.1+i*0.52
      @ents.add_line(pt(xx,-0.52,5.27),pt(xx+0.22,-0.52,5.36)).material=mat("Terracotta")
    end
  end

  def build_arch_outline(cx,y,z,width,height,label)
    g=@ents.add_group; g.name=label; e=g.entities
    r=width/2.0
    e.add_line(pt(cx-r,y,z),pt(cx-r,y,z+height-r))
    16.times do |i|
      a=Math::PI*i/16.0; b=Math::PI*(i+1)/16.0
      e.add_line(pt(cx+r*Math.cos(a),y,z+height-r+r*Math.sin(a)),
                 pt(cx+r*Math.cos(b),y,z+height-r+r*Math.sin(b)))
    end
    e.add_line(pt(cx+r,y,z),pt(cx+r,y,z+height-r))
    g
  end

  def build_tower_roof
    g=@ents.add_group; g.name="Upturned red tower roof"; e=g.entities
    # Four roof planes slope upward at corners, with a shallow central crown.
    corners=[[-4.5,-1.25,16.55],[4.5,-1.25,16.55],[4.5,7.2,16.55],[-4.5,7.2,16.55]]
    center=pt(0,2.95,16.95)
    pts=corners.map{|a|pt(*a)}
    4.times do |i|
      f=e.add_face(pts[i],pts[(i+1)%4],center)
      f.material=mat("Tile"); f.back_material=mat("Tile")
    end
    # Raised/eaved corners for the East Asian-inspired roof profile
    4.times do |i|
      a=pts[i]
      b=pts[(i+1)%4]
      e.add_line(a,b).material=mat("Tile light")
      tip=pt(a.x.to_m*1.03, a.y.to_m*1.03, 17.05)
      e.add_line(a,tip).material=mat("Tile light")
    end
    g
  end
end

MotherOfPerpetualHelpParish.run
