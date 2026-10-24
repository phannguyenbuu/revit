import ezdxf
from ezdxf.bbox import extents
import numpy as np
import os
import shutil
from pathlib import Path

import sys

# Load full floorplan DXF
dxf_candidates = [
    sys.argv[1] if len(sys.argv) > 1 else None,
    os.path.join(os.path.dirname(__file__), "clipboard_converted.dxf") if "__file__" in locals() else None,
    os.path.join(os.path.dirname(__file__), "ramp_extracted.dxf") if "__file__" in locals() else None,
    r"C:\Users\Admin\.gemini\antigravity\scratch\clipboard_converted.dxf",
    os.path.join(Path.home(), "Downloads", "AutoCAD_3D_OBJ", "clipboard_converted.dxf"),
    os.path.join(Path.home(), "Downloads", "clipboard_converted.dxf")
]

dxf_path = None
for c in dxf_candidates:
    if c and os.path.exists(c):
        dxf_path = c
        break

if not dxf_path:
    raise FileNotFoundError("Không tìm thấy tệp DXF đầu vào!")

print(f"Loading floorplan DXF: {dxf_path}")
doc = ezdxf.readfile(dxf_path)
msp = doc.modelspace()

bb = extents(msp)
min_x = bb.extmin.x
min_y = bb.extmin.y
max_x = bb.extmax.x
max_y = bb.extmax.y

BUILDING_X_MIN = 407000.0
BUILDING_X_MAX = 454000.0
BUILDING_Y_MIN = -1493000.0
BUILDING_Y_MAX = -1473000.0

origin_x = BUILDING_X_MIN
origin_y = BUILDING_Y_MIN

# 1. Stair Core Definitions (West & East shafts)
stair_cores = [
    {
        "name": "Stair_West",
        "box": (418000.0, -1482800.0, 422500.0, -1475300.0),
        "x_left_min": 418425.4,
        "x_left_max": 419800.4,
        "x_right_min": 420550.4,
        "x_right_max": 421925.4,
        "x_shaft_left": 418425.4,
        "x_shaft_right": 422125.4,
        "y_bottom": -1480300.0,
        "y_top": -1477250.0,
        "y_landing_top": -1475380.0,
        "y_shaft_bottom": -1482680.0
    },
    {
        "name": "Stair_East",
        "box": (443200.0, -1482800.0, 447700.0, -1475300.0),
        "x_left_min": 443625.4,
        "x_left_max": 445000.4,
        "x_right_min": 445750.4,
        "x_right_max": 447125.4,
        "x_shaft_left": 443625.4,
        "x_shaft_right": 447325.4,
        "y_bottom": -1480300.0,
        "y_top": -1477250.0,
        "y_landing_top": -1475380.0,
        "y_shaft_bottom": -1482680.0
    }
]

# 2. Tam Cap (Entrance Steps) Definitions
tam_cap_zones = [
    {
        "name": "Tam_Cap_Tien_Sanh_Tay",
        "description": "Bậc tam cấp sảnh chính phía Tây",
        "box": (408500.0, -1486000.0, 410200.0, -1481500.0),
        "type": "stepped_x",
        "x_steps": [408749.5, 409049.5, 409349.5, 409649.5, 409949.5],
        "y_min": -1485578.5,
        "y_max": -1481978.5,
        "direction": "+x"
    },
    {
        "name": "Tam_Cap_Phu_Tay",
        "description": "Bậc tam cấp sảnh phụ phía Tây (bước theo trục Y, đã đảo chiều lên xuống)",
        "box": (410000.0, -1481500.0, 414000.0, -1480000.0),
        "type": "stepped_y",
        "y_steps": [-1480378.5, -1480678.5, -1480978.5, -1481278.5],
        "x_min": 410225.4,
        "x_max": 413725.4,
        "direction": "-y"
    },
    {
        "name": "Tam_Cap_Sanh_Dong",
        "description": "Bậc tam cấp sảnh thoát hiểm phía Đông",
        "box": (452000.0, -1485200.0, 454000.0, -1482400.0),
        "type": "stepped_x",
        "x_steps": [453525.4, 453225.4, 452925.4, 452625.4, 452325.4],
        "y_min": -1484878.5,
        "y_max": -1482678.5,
        "direction": "-x"
    }
]

def in_stair_zone(x, y):
    for s in stair_cores:
        bx1, by1, bx2, by2 = s["box"]
        if bx1 <= x <= bx2 and by1 <= y <= by2:
            return s
    return None

def in_tam_cap_zone(x, y):
    for tc in tam_cap_zones:
        bx1, by1, bx2, by2 = tc["box"]
        if bx1 <= x <= bx2 and by1 <= y <= by2:
            return tc
    return None

# 3. Slope Ramp (Ram Dốc) Definition
ramp_zones = [
    {
        "name": "Ramp_Tien_Sanh_Tay",
        "description": "Đường dốc (slope ramp) cho người khuyết tật/xe đẩy lối sảnh chính phía Tây",
        "box": (409500.0, -1491500.0, 414500.0, -1485500.0),
        "x_left": 410225.4,
        "x_right": 413725.4,
        "y_start": -1491278.5,
        "y_end": -1485678.5,
        "z_start": 0.0,
        "z_end": 600.0,
        "curb_width": 100.0,
        "curb_height": 150.0
    }
]

def in_ramp_zone(x, y):
    for r in ramp_zones:
        bx1, by1, bx2, by2 = r["box"]
        if bx1 <= x <= bx2 and by1 <= y <= by2:
            return r
    return None

def is_valid_segment(p1, p2):
    return (BUILDING_X_MIN <= p1[0] <= BUILDING_X_MAX and 
            BUILDING_Y_MIN <= p1[1] <= BUILDING_Y_MAX and
            BUILDING_X_MIN <= p2[0] <= BUILDING_X_MAX and 
            BUILDING_Y_MIN <= p2[1] <= BUILDING_Y_MAX)

def extract_segments(e):
    t = e.dxftype()
    raw_segs = []
    if t == "LINE":
        raw_segs.append(((e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)))
    elif t == "LWPOLYLINE":
        pts = list(e.get_points())
        closed = e.closed
        for i in range(len(pts) - 1):
            raw_segs.append(((pts[i][0], pts[i][1]), (pts[i+1][0], pts[i+1][1])))
        if closed and len(pts) > 2:
            raw_segs.append(((pts[-1][0], pts[-1][1]), (pts[0][0], pts[0][1])))
    elif t == "ARC":
        c = (e.dxf.center.x, e.dxf.center.y)
        r = e.dxf.radius
        sa = np.radians(e.dxf.start_angle)
        ea = np.radians(e.dxf.end_angle)
        if ea < sa:
            ea += 2 * np.pi
        steps = max(12, int(np.degrees(ea - sa) / 8))
        angles = np.linspace(sa, ea, steps + 1)
        arc_pts = [(c[0] + r * np.cos(a), c[1] + r * np.sin(a)) for a in angles]
        for i in range(len(arc_pts) - 1):
            raw_segs.append((arc_pts[i], arc_pts[i+1]))
    elif t == "CIRCLE":
        c = (e.dxf.center.x, e.dxf.center.y)
        r = e.dxf.radius
        angles = np.linspace(0, 2*np.pi, 24, endpoint=False)
        circ_pts = [(c[0] + r * np.cos(a), c[1] + r * np.sin(a)) for a in angles]
        for i in range(len(circ_pts)):
            raw_segs.append((circ_pts[i], circ_pts[(i+1)%len(circ_pts)]))
    elif t == "INSERT":
        try:
            for sub_e in e.virtual_entities():
                raw_segs.extend(extract_segments(sub_e))
        except:
            pass
    return [s for s in raw_segs if is_valid_segment(s[0], s[1])]

# Filter entities into categories
wall_segments = []
column_segments = []
door_segments = []
door_arcs = []
window_segments = []

for e in msp:
    layer = e.dxf.layer.upper()
    try:
        ebb = extents([e])
        cx = (ebb.extmin.x + ebb.extmax.x) / 2
        cy = (ebb.extmin.y + ebb.extmax.y) / 2
    except:
        continue

    # Exclude stray entities outside building
    if not (BUILDING_X_MIN <= cx <= BUILDING_X_MAX and BUILDING_Y_MIN <= cy <= BUILDING_Y_MAX):
        continue

    # Exclude entities inside stair zones, tam cap zones, or ramp zones from wall/door/window
    if in_stair_zone(cx, cy) or in_tam_cap_zone(cx, cy) or in_ramp_zone(cx, cy):
        continue

    # Doors
    if any(k in layer for k in ["A-DOOR", "32-CUA", "CUA"]) and not any(k in layer for k in ["CUA SO", "CUA-SO"]):
        if e.dxftype() == "ARC":
            door_arcs.extend(extract_segments(e))
        else:
            door_segments.extend(extract_segments(e))

    # Windows
    elif any(k in layer for k in ["CUA SO", "CUA-SO", "WINDOW"]):
        window_segments.extend(extract_segments(e))

    # Columns
    elif any(k in layer for k in ["COT", "COLU"]):
        column_segments.extend(extract_segments(e))

    # Walls
    elif any(k in layer for k in ["TUONG", "A-WALL", "WALL", "S5", "NET03", "NET-02", "N THAY 0.25", "LAYERMANH"]):
        wall_segments.extend(extract_segments(e))

print(f"Extracted architectural elements:")
print(f"  Walls: {len(wall_segments)}")
print(f"  Columns: {len(column_segments)}")
print(f"  Doors: {len(door_segments)} lines + {len(door_arcs)} arc segments")
print(f"  Windows: {len(window_segments)}")

# OBJ Mesh Builder Class
class ObjMeshBuilder:
    def __init__(self, name, scale=0.001, offset=(origin_x, origin_y, 0)):
        self.name = name
        self.scale = scale
        self.ox, self.oy, self.oz = offset
        self.vertices = []
        self.faces = []
        self.material = None

    def transform(self, x, y, z):
        tx = (x - self.ox) * self.scale
        ty = (y - self.oy) * self.scale
        tz = (z - self.oz) * self.scale
        return tx, ty, tz

    def add_quad(self, p1, p2, p3, p4, double_sided=True):
        idx = len(self.vertices) + 1
        self.vertices.append(self.transform(*p1))
        self.vertices.append(self.transform(*p2))
        self.vertices.append(self.transform(*p3))
        self.vertices.append(self.transform(*p4))
        self.faces.append((idx, idx+1, idx+2, idx+3))
        if double_sided:
            self.faces.append((idx+3, idx+2, idx+1, idx))

    def add_box(self, x1, y1, z1, x2, y2, z2):
        self.add_quad((x1, y1, z1), (x2, y1, z1), (x2, y2, z1), (x1, y2, z1))
        self.add_quad((x1, y1, z2), (x2, y1, z2), (x2, y2, z2), (x1, y2, z2))
        self.add_quad((x1, y1, z1), (x2, y1, z1), (x2, y1, z2), (x1, y1, z2))
        self.add_quad((x2, y1, z1), (x2, y2, z1), (x2, y2, z2), (x2, y1, z2))
        self.add_quad((x2, y2, z1), (x1, y2, z1), (x1, y2, z2), (x2, y2, z2))
        self.add_quad((x1, y2, z1), (x1, y1, z1), (x1, y1, z2), (x1, y2, z2))

    def add_vertical_wall(self, p1_2d, p2_2d, z_bottom, z_top, double_sided=True):
        v1 = (p1_2d[0], p1_2d[1], z_bottom)
        v2 = (p2_2d[0], p2_2d[1], z_bottom)
        v3 = (p2_2d[0], p2_2d[1], z_top)
        v4 = (p1_2d[0], p1_2d[1], z_top)
        self.add_quad(v1, v2, v3, v4, double_sided=double_sided)

    def add_horizontal_quad(self, p1_2d, p2_2d, p3_2d, p4_2d, z, double_sided=True):
        v1 = (p1_2d[0], p1_2d[1], z)
        v2 = (p2_2d[0], p2_2d[1], z)
        v3 = (p3_2d[0], p3_2d[1], z)
        v4 = (p4_2d[0], p4_2d[1], z)
        self.add_quad(v1, v2, v3, v4, double_sided=double_sided)

    def add_thickened_ribbon(self, p1_2d, p2_2d, z, width=40.0):
        x1, y1 = p1_2d
        x2, y2 = p2_2d
        dx, dy = x2 - x1, y2 - y1
        L = np.hypot(dx, dy)
        if L < 1e-4:
            return
        nx, ny = -dy / L * (width/2), dx / L * (width/2)
        v1 = (x1 - nx, y1 - ny, z)
        v2 = (x2 - nx, y2 - ny, z)
        v3 = (x2 + nx, y2 + ny, z)
        v4 = (x1 + nx, y1 + ny, z)
        self.add_quad(v1, v2, v3, v4, double_sided=True)

    def write_obj(self, filepath, mtl_filename=None):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Wavefront OBJ File\n")
            f.write(f"# Object Name: {self.name}\n")
            f.write(f"# Scale: 1 unit = {'1 meter' if self.scale == 0.001 else '1 mm'}\n")
            if mtl_filename:
                f.write(f"mtllib {mtl_filename}\n")
            f.write(f"o {self.name}\n")
            if self.material:
                f.write(f"usemtl {self.material}\n")
            for v in self.vertices:
                f.write(f"v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n")
            for face in self.faces:
                f.write(f"f {' '.join(str(idx) for idx in face)}\n")

# 1. WALL MESH
def build_wall_mesh(scale, offset):
    mesh = ObjMeshBuilder("Wall", scale=scale, offset=offset)
    mesh.material = "mat_wall"
    wall_h = 3000.0
    for p1, p2 in wall_segments:
        mesh.add_vertical_wall(p1, p2, 0.0, wall_h)
    for p1, p2 in column_segments:
        mesh.add_vertical_wall(p1, p2, 0.0, wall_h)
    return mesh

# 2. DOOR MESH
def build_door_mesh(scale, offset):
    mesh = ObjMeshBuilder("Door", scale=scale, offset=offset)
    mesh.material = "mat_door"
    door_h = 2100.0
    wall_h = 3000.0
    for p1, p2 in door_segments:
        mesh.add_vertical_wall(p1, p2, 0.0, door_h)
        mesh.add_vertical_wall(p1, p2, door_h, wall_h)
    for p1, p2 in door_arcs:
        mesh.add_thickened_ribbon(p1, p2, z=15.0, width=30.0)
    return mesh

# 3. WINDOW MESH (cleansed of tam cap lines)
def build_window_mesh(scale, offset):
    mesh = ObjMeshBuilder("Window", scale=scale, offset=offset)
    mesh.material = "mat_window"
    sill_h = 900.0
    head_h = 2200.0
    wall_h = 3000.0
    for p1, p2 in window_segments:
        mesh.add_vertical_wall(p1, p2, 0.0, sill_h)
        mesh.add_vertical_wall(p1, p2, sill_h, head_h)
        mesh.add_vertical_wall(p1, p2, head_h, wall_h)
    return mesh

# 4. STAIR MESH (Internal Staircases + 3 Tam Cap Entrance Steps)
def build_stair_mesh(scale, offset):
    mesh = ObjMeshBuilder("Stair", scale=scale, offset=offset)
    mesh.material = "mat_stair"
    
    # A. 2 INTERNAL STAIRCASES
    num_steps = 11
    flight1_h = 1500.0
    flight2_h = 3000.0
    dz = flight1_h / num_steps

    for sc in stair_cores:
        x_left = sc["x_shaft_left"]
        x_right = sc["x_shaft_right"]
        y_bottom = sc["y_shaft_bottom"]
        y_top = sc["y_landing_top"]
        
        # Shaft walls
        mesh.add_vertical_wall((x_left, y_bottom), (x_left, y_top), 0.0, 3000.0)
        mesh.add_vertical_wall((x_right, y_bottom), (x_right, y_top), 0.0, 3000.0)
        mesh.add_vertical_wall((x_left, y_top), (x_right, y_top), 0.0, 3000.0)
        
        # Entrance landing
        mesh.add_horizontal_quad((x_left, y_bottom), (x_right, y_bottom), (x_right, sc["y_bottom"]), (x_left, sc["y_bottom"]), z=0.0)

        # Intermediate Landing Slab
        y_l_start = sc["y_top"]
        y_l_end = sc["y_landing_top"]
        mesh.add_horizontal_quad((x_left, y_l_start), (x_right, y_l_start), (x_right, y_l_end), (x_left, y_l_end), z=flight1_h)
        mesh.add_vertical_wall((x_left, y_l_start), (x_right, y_l_start), flight1_h - 150.0, flight1_h)

        # Flight 1
        xl1 = sc["x_left_min"]
        xl2 = sc["x_left_max"]
        y_step_pitch = (sc["y_top"] - sc["y_bottom"]) / num_steps

        for i in range(num_steps):
            y_s = sc["y_bottom"] + i * y_step_pitch
            y_e = sc["y_bottom"] + (i + 1) * y_step_pitch
            z_s = i * dz
            z_e = (i + 1) * dz
            mesh.add_vertical_wall((xl1, y_s), (xl2, y_s), z_s, z_e)
            mesh.add_horizontal_quad((xl1, y_s), (xl2, y_s), (xl2, y_e), (xl1, y_e), z=z_e)

        mesh.add_vertical_wall((xl2, sc["y_bottom"]), (xl2, sc["y_top"]), 0.0, flight1_h + 900.0)

        # Flight 2
        xr1 = sc["x_right_min"]
        xr2 = sc["x_right_max"]

        for i in range(num_steps):
            y_s = sc["y_top"] - i * y_step_pitch
            y_e = sc["y_top"] - (i + 1) * y_step_pitch
            z_s = flight1_h + i * dz
            z_e = flight1_h + (i + 1) * dz
            mesh.add_vertical_wall((xr1, y_s), (xr2, y_s), z_s, z_e)
            mesh.add_horizontal_quad((xr1, y_s), (xr2, y_s), (xr2, y_e), (xr1, y_e), z=z_e)

        mesh.add_vertical_wall((xr1, sc["y_top"]), (xr1, sc["y_bottom"]), flight1_h, flight2_h + 900.0)
        mesh.add_vertical_wall((xl2, sc["y_top"]), (xr1, sc["y_top"]), flight1_h, flight1_h + 900.0)
        mesh.add_box(xl2 - 60.0, sc["y_bottom"] - 60.0, 0.0, xl2 + 60.0, sc["y_bottom"] + 60.0, 1000.0)

    # B. 3 TAM CAP (ENTRANCE STEPS)
    riser_h = 150.0  # 150mm per step riser
    
    for tc in tam_cap_zones:
        if tc["type"] == "stepped_x":
            steps_x = tc["x_steps"]
            y1, y2 = tc["y_min"], tc["y_max"]
            n = len(steps_x) - 1

            if "landing_x" in tc:
                lx1, lx2 = tc["landing_x"]
                mesh.add_horizontal_quad((lx1, y1), (lx2, y1), (lx2, y2), (lx1, y2), z=0.0)
            
            for i in range(n):
                sx1 = steps_x[i]
                sx2 = steps_x[i+1]
                z_cur = (i + 1) * riser_h
                z_prev = i * riser_h
                # Riser at sx1
                mesh.add_vertical_wall((sx1, y1), (sx1, y2), z_prev, z_cur)
                # Tread from sx1 to sx2
                mesh.add_horizontal_quad((sx1, y1), (sx1, y2), (sx2, y2), (sx2, y1), z=z_cur)
                # Side cheeks
                mesh.add_vertical_wall((sx1, y1), (sx2, y1), 0.0, z_cur)
                mesh.add_vertical_wall((sx1, y2), (sx2, y2), 0.0, z_cur)
            
            # End wall at top step sx2
            mesh.add_vertical_wall((steps_x[-1], y1), (steps_x[-1], y2), 0.0, n * riser_h)
                    
        elif tc["type"] == "stepped_y":
            steps_y = tc["y_steps"]
            x1, x2 = tc["x_min"], tc["x_max"]
            n = len(steps_y) - 1
            for i in range(n):
                sy1 = steps_y[i]
                sy2 = steps_y[i+1]
                z_cur = (i + 1) * riser_h
                z_prev = i * riser_h
                # Riser at sy1
                mesh.add_vertical_wall((x1, sy1), (x2, sy1), z_prev, z_cur)
                # Tread from sy1 to sy2
                mesh.add_horizontal_quad((x1, sy1), (x2, sy1), (x2, sy2), (x1, sy2), z=z_cur)
                # Side cheeks
                mesh.add_vertical_wall((x1, sy1), (x1, sy2), 0.0, z_cur)
                mesh.add_vertical_wall((x2, sy1), (x2, sy2), 0.0, z_cur)

    # C. 1 SLOPE RAMP (RAM DỐC TIỀN SẢNH)
    for r in ramp_zones:
        add_ramp_to_mesh(mesh, r)

    return mesh

def add_ramp_to_mesh(mesh, r):
    x_left = r["x_left"]
    x_right = r["x_right"]
    y_start = r["y_start"]
    y_end = r["y_end"]
    z_start = r["z_start"]
    z_end = r["z_end"]
    curb_w = r["curb_width"]
    curb_h = r["curb_height"]

    # 1. Main sloped continuous quad surface
    v1 = (x_left, y_start, z_start)
    v2 = (x_right, y_start, z_start)
    v3 = (x_right, y_end, z_end)
    v4 = (x_left, y_end, z_end)
    mesh.add_quad(v1, v2, v3, v4, double_sided=True)

    # 2. Side skirts (vertical cheek walls from ground 0 to slope surface)
    mesh.add_quad((x_left, y_start, 0.0), (x_left, y_end, 0.0), (x_left, y_end, z_end), (x_left, y_start, z_start), double_sided=True)
    mesh.add_quad((x_right, y_start, 0.0), (x_right, y_end, 0.0), (x_right, y_end, z_end), (x_right, y_start, z_start), double_sided=True)

    # 3. Top end wall abutting porch
    mesh.add_quad((x_left, y_end, 0.0), (x_right, y_end, 0.0), (x_right, y_end, z_end), (x_left, y_end, z_end), double_sided=True)

    # 4. Left curb (gờ chắn bánh xe bên trái)
    xl_out = x_left - curb_w
    mesh.add_quad((xl_out, y_start, z_start + curb_h), (x_left, y_start, z_start + curb_h), (x_left, y_end, z_end + curb_h), (xl_out, y_end, z_end + curb_h), double_sided=True)
    mesh.add_quad((xl_out, y_start, 0.0), (xl_out, y_end, 0.0), (xl_out, y_end, z_end + curb_h), (xl_out, y_start, z_start + curb_h), double_sided=True)
    mesh.add_quad((x_left, y_start, z_start), (x_left, y_end, z_end), (x_left, y_end, z_end + curb_h), (x_left, y_start, z_start + curb_h), double_sided=True)
    mesh.add_quad((xl_out, y_start, 0.0), (x_left, y_start, 0.0), (x_left, y_start, z_start + curb_h), (xl_out, y_start, z_start + curb_h), double_sided=True)
    mesh.add_quad((xl_out, y_end, 0.0), (x_left, y_end, 0.0), (x_left, y_end, z_end + curb_h), (xl_out, y_end, z_end + curb_h), double_sided=True)

    # 5. Right curb (gờ chắn bánh xe bên phải)
    xr_out = x_right + curb_w
    mesh.add_quad((x_right, y_start, z_start + curb_h), (xr_out, y_start, z_start + curb_h), (xr_out, y_end, z_end + curb_h), (x_right, y_end, z_end + curb_h), double_sided=True)
    mesh.add_quad((xr_out, y_start, 0.0), (xr_out, y_end, 0.0), (xr_out, y_end, z_end + curb_h), (xr_out, y_start, z_start + curb_h), double_sided=True)
    mesh.add_quad((x_right, y_start, z_start), (x_right, y_end, z_end), (x_right, y_end, z_end + curb_h), (x_right, y_start, z_start + curb_h), double_sided=True)
    mesh.add_quad((x_right, y_start, 0.0), (xr_out, y_start, 0.0), (xr_out, y_start, z_start + curb_h), (x_right, y_start, z_start + curb_h), double_sided=True)
    mesh.add_quad((x_right, y_end, 0.0), (xr_out, y_end, 0.0), (xr_out, y_end, z_end + curb_h), (x_right, y_end, z_end + curb_h), double_sided=True)

# 5. RAMP MESH (Standalone)
def build_ramp_mesh(scale, offset):
    mesh = ObjMeshBuilder("Ramp", scale=scale, offset=offset)
    mesh.material = "mat_stair"
    for r in ramp_zones:
        add_ramp_to_mesh(mesh, r)
    return mesh

# Generate MTL Material File
def write_mtl(filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# Materials for Architectural Floorplan\n\n")
        f.write("newmtl mat_wall\n")
        f.write("Kd 0.85 0.85 0.85\nKa 0.2 0.2 0.2\nKs 0.1 0.1 0.1\nNs 10.0\nd 1.0\n\n")
        f.write("newmtl mat_door\n")
        f.write("Kd 0.65 0.35 0.15\nKa 0.2 0.1 0.05\nKs 0.2 0.2 0.2\nNs 20.0\nd 1.0\n\n")
        f.write("newmtl mat_window\n")
        f.write("Kd 0.35 0.75 0.95\nKa 0.1 0.2 0.3\nKs 0.8 0.8 0.8\nNs 50.0\nd 0.6\n\n")
        f.write("newmtl mat_stair\n")
        f.write("Kd 0.85 0.55 0.20\nKa 0.25 0.15 0.05\nKs 0.3 0.3 0.3\nNs 20.0\nd 1.0\n\n")

# Output folders
out_m = r"C:\Users\Admin\.gemini\antigravity\scratch\obj_export_meters"
out_mm = r"C:\Users\Admin\.gemini\antigravity\scratch\obj_export_cad_mm"

configs = [
    ("meters", 0.001, (origin_x, origin_y, 0), out_m),
    ("cad_mm", 1.0, (0, 0, 0), out_mm)
]

for label, scale, offset, folder in configs:
    mtl_name = "materials.mtl"
    write_mtl(os.path.join(folder, mtl_name))
    
    w_mesh = build_wall_mesh(scale, offset)
    w_mesh.write_obj(os.path.join(folder, "wall.obj"), mtl_name)
    
    d_mesh = build_door_mesh(scale, offset)
    d_mesh.write_obj(os.path.join(folder, "door.obj"), mtl_name)
    
    win_mesh = build_window_mesh(scale, offset)
    win_mesh.write_obj(os.path.join(folder, "window.obj"), mtl_name)
    
    s_mesh = build_stair_mesh(scale, offset)
    s_mesh.write_obj(os.path.join(folder, "stair.obj"), mtl_name)

    r_mesh = build_ramp_mesh(scale, offset)
    r_mesh.write_obj(os.path.join(folder, "ramp.obj"), mtl_name)

    # Combined full building model
    full_path = os.path.join(folder, "building_full.obj")
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(f"# Complete Architectural 3D Model with 3 Tam Cap, Slope Ramp & Corrected Stairs\n")
        f.write(f"mtllib {mtl_name}\n\n")
        
        v_offset = 0
        for m in [w_mesh, d_mesh, win_mesh, s_mesh]:
            f.write(f"o {m.name}\n")
            f.write(f"usemtl {m.material}\n")
            for v in m.vertices:
                f.write(f"v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n")
            for face in m.faces:
                f.write(f"f {' '.join(str(idx + v_offset) for idx in face)}\n")
            v_offset += len(m.vertices)
    print(f"Exported [{label}] combined model with Tam Cap & Ramp -> {full_path}")

# Copy to ~/Downloads
downloads = Path.home() / "Downloads"
dest_dir = downloads / "AutoCAD_3D_OBJ"
dest_dir.mkdir(parents=True, exist_ok=True)

for f in Path(out_m).glob("*"):
    shutil.copy2(f, dest_dir / f.name)
    shutil.copy2(f, downloads / f.name)

dest_mm = dest_dir / "cad_mm"
dest_mm.mkdir(exist_ok=True)
for f in Path(out_mm).glob("*"):
    shutil.copy2(f, dest_mm / f.name)

print("\nSuccessfully updated files in ~/Downloads and ~/Downloads/AutoCAD_3D_OBJ!")
