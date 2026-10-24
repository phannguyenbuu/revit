"""
SketchUp Ruby (.rb) to 3D Wavefront OBJ Converter & Execution Engine
Author: Antigravity Assistant
Description:
1. Emulates SketchUp Ruby API in Python:
   - Geom::Point3d, Geom::Vector3d, Geom::Transformation
   - Sketchup.active_model (entities, materials, layers, groups, faces, selection, active_view, camera)
   - Face pushpull, reverse, normal calculation, circle generation with arbitrary normals
   - Box, cylinder, circle, and opening creation, 3D text approximation
   - Metric units: .m, .mm, .cm, .inch, .degrees, .to_m, .to_mm, .to_cm
2. Transpiles Ruby syntax (def, end, blocks, symbols, loops, trailing if/unless, ternary, implicit return) to executable Python
3. Exports high-fidelity Wavefront .obj and .mtl materials
4. Provides full geometry inspection via Trimesh
"""

import sys
import os
import re
import json
import shutil
import math
from pathlib import Path

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
RUBY_DIR = CURRENT_DIR
RUBY_EXPORTS_DIR = os.path.join(CURRENT_DIR, "ruby_exports")
os.makedirs(RUBY_EXPORTS_DIR, exist_ok=True)


# ==============================================================================
# 1. GEOMETRIC CORE & SKETCHUP API MOCK CLASSES
# ==============================================================================

class _FirstElement:
    def __init__(self, lst):
        self._lst = lst

    def __call__(self, n=None):
        if n is None:
            return self._lst[0] if len(self._lst) > 0 else None
        return RubyList(self._lst[:int(n)])

    def __getattr__(self, name):
        if not self._lst or len(self._lst) == 0:
            return None
        return getattr(self._lst[0], name)

    def __setattr__(self, name, value):
        if name == '_lst':
            super().__setattr__(name, value)
        elif self._lst and len(self._lst) > 0:
            setattr(self._lst[0], name, value)

    def __getitem__(self, idx):
        if not self._lst or len(self._lst) == 0:
            return None
        return self._lst[0][idx]

    def __bool__(self):
        return bool(self._lst and len(self._lst) > 0 and self._lst[0] is not None)

    def __repr__(self):
        return repr(self._lst[0] if len(self._lst) > 0 else None)

    def __str__(self):
        return str(self._lst[0] if len(self._lst) > 0 else "")


class _LastElement(_FirstElement):
    def __call__(self, n=None):
        if n is None:
            return self._lst[-1] if len(self._lst) > 0 else None
        return RubyList(self._lst[-int(n):])

    def __getattr__(self, name):
        if not self._lst or len(self._lst) == 0:
            return None
        return getattr(self._lst[-1], name)

    def __setattr__(self, name, value):
        if name == '_lst':
            super().__setattr__(name, value)
        elif self._lst and len(self._lst) > 0:
            setattr(self._lst[-1], name, value)

    def __repr__(self):
        return repr(self._lst[-1] if len(self._lst) > 0 else None)

    def __str__(self):
        return str(self._lst[-1] if len(self._lst) > 0 else "")


class Edge:
    def __init__(self, start=None, end=None, parent_face=None):
        if start is not None and not isinstance(start, Vertex):
            start = Vertex(start)
        if end is not None and not isinstance(end, Vertex):
            end = Vertex(end)
        self.start = start
        self.end = end
        self._faces = [parent_face] if parent_face else []
        self.soft = False
        self.smooth = False
        self.hidden = False
        self.material = None

    def __iter__(self):
        yield self

    @property
    def faces(self):
        return RubyList(self._faces)

    @property
    def p1(self):
        return self.start

    @property
    def p2(self):
        return self.end

    def length(self):
        if self.start and self.end:
            return self.start.distance(self.end)
        return 0.0

    @property
    def vertices(self):
        return RubyList([self.start, self.end] if self.start and self.end else [])

    @property
    def position(self):
        return self.start.position if self.start else Point3d(0, 0, 0)

    @property
    def x(self):
        return self.position.x

    @property
    def y(self):
        return self.position.y

    @property
    def z(self):
        return self.position.z

    def __getitem__(self, idx):
        return [self.position.x, self.position.y, self.position.z][idx]

    def find_faces(self):
        return 1

    @property
    def bounds(self):
        return BoundingBoxMock()

    def pushpull(self, *args):
        return self

    def move_bang(self, *args):
        return self

    def transform_bang(self, *args):
        return self

    def erase_bang(self, *args):
        pass

    def valid(self):
        return True

    def deleted(self):
        return False

    def other_vertex(self, v):
        return self.end if v == self.start else self.start

    @property
    def entities(self):
        return self._faces[0].parent if self._faces and hasattr(self._faces[0], 'parent') else Entities()

    def line(self):
        return [self.start, self.end]

    def __repr__(self):
        return f"Edge({self.start} -> {self.end})"


class RubyList(list):
    """Mở rộng list chuẩn của Python để hỗ trợ toán tử và phương thức của mảng Ruby."""
    def __getitem__(self, idx):
        if isinstance(idx, tuple) and len(idx) == 2:
            start = int(idx[0])
            length = int(idx[1])
            if start < 0:
                end = start + length
                return RubyList(list(self)[start:] if end == 0 else list(self)[start:end])
            return RubyList(list(self)[start : start + length])
        res = super().__getitem__(idx)
        if isinstance(res, list):
            return RubyList(res)
        return res

    def __call__(self, *args):
        return self

    def __lshift__(self, item):
        self.append(item)
        return self

    def compact(self):
        return RubyList([x for x in self if x is not None])

    def uniq(self):
        return RubyList(list(dict.fromkeys(self)))

    def reverse(self):
        return RubyList(list(reversed(self)))

    @property
    def start(self):
        if len(self) > 0:
            first = self[0]
            if hasattr(first, 'start'):
                return first.start
            return first
        return None

    @property
    def position(self):
        if len(self) > 0:
            first = self[0]
            if hasattr(first, 'position'):
                return first.position
            return first
        return None

    def grep(self, cls):
        return RubyList([x for x in self if isinstance(x, cls)])

    def each(self, fn=None):
        if fn:
            for x in self:
                fn(x)
        return self

    def map(self, fn):
        return RubyList([fn(x) for x in self])

    def select(self, fn=None):
        if fn is None:
            return self
        return RubyList([x for x in self if fn(x)])

    def find_all(self, fn=None):
        return self.select(fn)

    def reject(self, fn=None):
        if fn is None:
            return self
        return RubyList([x for x in self if not fn(x)])

    def collect(self, fn):
        return self.map(fn)

    def length(self):
        return len(self)

    def max(self):
        return max(self) if self else None

    def min(self):
        return min(self) if self else None

    @property
    def first(self):
        return _FirstElement(self)

    @property
    def last(self):
        return _LastElement(self)

    def join(self, delim=""):
        return str(delim).join(str(x) for x in self)


class Color:
    def __init__(self, r=200, g=200, b=200, a=255):
        if isinstance(r, (list, tuple)):
            vals = list(r)
            self.r = vals[0] if len(vals) > 0 else 200
            self.g = vals[1] if len(vals) > 1 else 200
            self.b = vals[2] if len(vals) > 2 else 200
            self.a = vals[3] if len(vals) > 3 else (g if isinstance(g, (int, float)) else 255)
        elif isinstance(r, str):
            s = r.strip()
            if s.startswith('#'):
                hex_str = s.lstrip('#')
                if len(hex_str) == 3:
                    hex_str = ''.join([c * 2 for c in hex_str])
                if len(hex_str) >= 6:
                    self.r = int(hex_str[0:2], 16)
                    self.g = int(hex_str[2:4], 16)
                    self.b = int(hex_str[4:6], 16)
                    self.a = int(hex_str[6:8], 16) if len(hex_str) >= 8 else (int(g) if isinstance(g, (int, float)) else 255)
                else:
                    self.r, self.g, self.b, self.a = 200, 200, 200, 255
            else:
                named = {
                    'red': (255, 0, 0), 'green': (0, 255, 0), 'blue': (0, 0, 255),
                    'white': (255, 255, 255), 'black': (0, 0, 0), 'yellow': (255, 255, 0),
                    'cyan': (0, 255, 255), 'magenta': (255, 0, 255), 'gray': (128, 128, 128),
                    'grey': (128, 128, 128), 'orange': (255, 165, 0), 'gold': (255, 215, 0),
                    'silver': (192, 192, 192), 'brown': (165, 42, 42)
                }
                c = named.get(s.lower(), (200, 200, 200))
                self.r, self.g, self.b = c
                self.a = int(g) if isinstance(g, (int, float)) else 255
        else:
            try:
                self.r = int(r)
                self.g = int(g)
                self.b = int(b)
                self.a = int(a)
            except Exception:
                self.r, self.g, self.b, self.a = 200, 200, 200, 255

    def to_rgb_norm(self):
        return (self.r / 255.0, self.g / 255.0, self.b / 255.0)

    def to_alpha_norm(self):
        return self.a / 255.0 if self.a > 1.0 else float(self.a)


class Material:
    def __init__(self, name, color=None, alpha=1.0):
        self.name = re.sub(r'[^\w\-]+', '_', str(name)).strip('_') or 'Material'
        self.color = color
        self.alpha = float(alpha)

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, val):
        if isinstance(val, Color):
            self._color = val
        elif isinstance(val, (list, tuple)):
            self._color = Color(*val)
        elif isinstance(val, str):
            self._color = Color(val)
        else:
            self._color = Color(200, 200, 200)

    @property
    def red(self):
        return self.color.r

    @property
    def green(self):
        return self.color.g

    @property
    def blue(self):
        return self.color.b


class MaterialsCollection(dict):
    def __getitem__(self, key):
        return self.get(key, None)

    def add(self, name):
        m = Material(name)
        self[name] = m
        return m


class Layer:
    def __init__(self, name):
        self.name = str(name)
        self.visible = True


class LayersCollection(dict):
    def __getitem__(self, key):
        return self.get(key, None)

    def add(self, name):
        ly = Layer(name)
        self[name] = ly
        return ly


class Vector3d:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        if isinstance(x, (list, tuple, Vector3d, Point3d)):
            self.x = float(x[0])
            self.y = float(x[1])
            self.z = float(x[2]) if len(x) > 2 else 0.0
        else:
            self.x = float(x)
            self.y = float(y)
            self.z = float(z)

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z

    def __getitem__(self, idx):
        return [self.x, self.y, self.z][idx]

    def length(self):
        return math.sqrt(self.x*self.x + self.y*self.y + self.z*self.z)

    def dot(self, other):
        return self.x * other[0] + self.y * other[1] + self.z * other[2]

    def cross(self, other):
        return Vector3d(
            self.y * other[2] - self.z * other[1],
            self.z * other[0] - self.x * other[2],
            self.x * other[1] - self.y * other[0]
        )

    def clone(self):
        return Vector3d(self.x, self.y, self.z)

    def normalize(self):
        L = self.length()
        if L < 1e-9:
            return Vector3d(0, 0, 1)
        return Vector3d(self.x / L, self.y / L, self.z / L)

    def normalize_bang(self):
        L = self.length()
        if L >= 1e-9:
            self.x /= L
            self.y /= L
            self.z /= L
        return self

    def parallel(self, other):
        return abs(abs(self.dot(other)) - (self.length() * (other.length() if hasattr(other, 'length') else 1.0))) < 1e-4

    def parallel_p(self, other):
        return self.parallel(other)

    def perpendicular(self, other):
        return abs(self.dot(other)) < 1e-4

    def perpendicular_p(self, other):
        return self.perpendicular(other)

    def set_length(self, val):
        self.normalize_bang()
        val_f = float(val)
        self.x *= val_f
        self.y *= val_f
        self.z *= val_f
        return self

    def __repr__(self):
        return f"Vector3d({self.x:.3f}, {self.y:.3f}, {self.z:.3f})"


class Point3d:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        if isinstance(x, (list, tuple, Point3d)):
            self.x = float(x[0])
            self.y = float(x[1])
            self.z = float(x[2]) if len(x) > 2 else 0.0
        else:
            self.x = float(x)
            self.y = float(y)
            self.z = float(z)

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z

    def __getitem__(self, idx):
        return [self.x, self.y, self.z][idx]

    def __add__(self, other):
        if isinstance(other, (Point3d, Vector3d, list, tuple)):
            return Point3d(self.x + other[0], self.y + other[1], self.z + other[2])
        return self

    def __sub__(self, other):
        if isinstance(other, (Point3d, Vector3d, list, tuple)):
            return Vector3d(self.x - other[0], self.y - other[1], self.z - other[2])
        return self

    def distance(self, other):
        dx = self.x - other[0]
        dy = self.y - other[1]
        dz = self.z - other[2]
        return math.sqrt(dx*dx + dy*dy + dz*dz)

    def vector_to(self, other):
        return Vector3d(other[0] - self.x, other[1] - self.y, other[2] - self.z)

    def clone(self):
        return Point3d(self.x, self.y, self.z)

    def to_tuple(self):
        return (self.x, self.y, self.z)

    def parallel(self, other):
        return abs(abs(self.dot(other)) - (self.length() * (other.length() if hasattr(other, 'length') else 1.0))) < 1e-4

    def parallel_p(self, other):
        return self.parallel(other)

    def perpendicular(self, other):
        return abs(self.dot(other)) < 1e-4

    def perpendicular_p(self, other):
        return self.perpendicular(other)

    def set_length(self, val):
        self.normalize_bang()
        val_f = float(val)
        self.x *= val_f
        self.y *= val_f
        self.z *= val_f
        return self

    def offset(self, vec, length=None):
        if length is not None:
            v = Vector3d(vec).normalize_bang()
            return Point3d(self.x + v.x * length, self.y + v.y * length, self.z + v.z * length)
        return Point3d(self.x + vec[0], self.y + vec[1], self.z + vec[2])

    def __repr__(self):
        return f"Point3d({self.x:.3f}, {self.y:.3f}, {self.z:.3f})"


class Vertex:
    def __init__(self, pt):
        self.position = pt if isinstance(pt, Point3d) else Point3d(pt)

    def __iter__(self):
        yield self.position.x
        yield self.position.y
        yield self.position.z

    def __getitem__(self, idx):
        return [self.position.x, self.position.y, self.position.z][idx]

    @property
    def x(self):
        return self.position.x

    @property
    def y(self):
        return self.position.y

    @property
    def z(self):
        return self.position.z

    @property
    def faces(self):
        return RubyList()

    @property
    def edges(self):
        return RubyList()

    @property
    def bounds(self):
        return BoundingBoxMock()

    @property
    def entities(self):
        return Entities()

    @property
    def loops(self):
        return RubyList()

    @property
    def used_by_faces(self):
        return RubyList()

    def valid(self):
        return True

    def deleted(self):
        return False

    def erase_bang(self, *args):
        pass

    def pushpull(self, *args):
        return self

    def transform_bang(self, *args):
        return self

    def move_bang(self, *args):
        if args and len(args) > 0:
            tr = args[0]
            if isinstance(tr, (list, tuple)) and len(tr) >= 3:
                self.position.x += float(tr[0])
                self.position.y += float(tr[1])
                self.position.z += float(tr[2])
            elif hasattr(tr, 'x') and hasattr(tr, 'y') and hasattr(tr, 'z'):
                self.position.x += float(tr.x)
                self.position.y += float(tr.y)
                self.position.z += float(tr.z)
        return self

    def __repr__(self):
        return f"Vertex({self.position.x:.3f}, {self.position.y:.3f}, {self.position.z:.3f})"


class Loop:
    def __init__(self, parent_face):
        self._face = parent_face

    @property
    def vertices(self):
        return self._face.vertices

    @property
    def edges(self):
        return self._face.edges

    @property
    def face(self):
        return self._face


class Face:
    def __init__(self, pts, material=None, parent_entities=None):
        clean_pts = []
        for p in pts:
            if isinstance(p, Point3d):
                clean_pts.append(p)
            elif isinstance(p, Vertex):
                clean_pts.append(p.position)
            elif isinstance(p, (list, tuple)):
                clean_pts.append(Point3d(*p))
        self.pts = clean_pts
        self.material = material
        self.back_material = material
        self.parent = parent_entities

    @property
    def vertices(self):
        return RubyList([Vertex(p) for p in self.pts])

    @property
    def normal(self):
        if len(self.pts) < 3:
            return Vector3d(0, 0, 1)
        nx = 0.0
        ny = 0.0
        nz = 0.0
        n = len(self.pts)
        for i in range(n):
            curr = self.pts[i]
            nxt = self.pts[(i + 1) % n]
            nx += (curr.y - nxt.y) * (curr.z + nxt.z)
            ny += (curr.z - nxt.z) * (curr.x + nxt.x)
            nz += (curr.x - nxt.x) * (curr.y + nxt.y)
        L = math.sqrt(nx*nx + ny*ny + nz*nz)
        if L < 1e-9:
            return Vector3d(0, 0, 1)
        return Vector3d(nx / L, ny / L, nz / L)

    def reverse_bang(self):
        self.pts.reverse()
        return self

    def valid(self):
        return True

    def deleted(self):
        return False

    def erase(self, *args):
        pass

    def erase_bang(self, *args):
        if self.parent and hasattr(self.parent, 'faces'):
            try:
                self.parent.faces.remove(self)
            except Exception:
                pass

    def move_bang(self, *args):
        if args and len(args) > 0:
            tr = args[0]
            if isinstance(tr, (list, tuple)) and len(tr) >= 3:
                dx, dy, dz = float(tr[0]), float(tr[1]), float(tr[2])
                for p in self.pts:
                    p.x += dx
                    p.y += dy
                    p.z += dz
        return self

    @property
    def all_connected(self):
        res = RubyList()
        res.append(self)
        res.extend(self.edges)
        if self.parent and hasattr(self.parent, 'faces'):
            for f in self.parent.faces:
                if f is not self:
                    res.append(f)
                    res.extend(f.edges)
        return res

    def followme(self, path=None, *args):
        return self

    @property
    def inner_loops(self):
        return RubyList()

    @property
    def outer_loop(self):
        return Loop(self)

    @property
    def loops(self):
        return RubyList([Loop(self)])

    @property
    def edges(self):
        result = RubyList()
        n = len(self.pts)
        for i in range(n):
            result.append(Edge(self.pts[i], self.pts[(i + 1) % n], parent_face=self))
        return result

    def transform_bang(self, *args):
        return self

    @property
    def bounds(self):
        return BoundingBoxMock()

    @property
    def entities(self):
        return self.parent if self.parent else Entities()

    @property
    def first(self):
        return self

    def offset(self, dist=0.01):
        return RubyList([Face(self.pts, material=self.material, parent_entities=self.parent)])

    def erase_inner_loop(self, *args):
        pass

    def __iter__(self):
        return iter(self.vertices)

    def pushpull(self, dist, *args):
        """Đùn mặt phẳng theo pháp tuyến một khoảng dist, tự động tạo thành khối hộp 3D."""
        if abs(dist) < 1e-6 or len(self.pts) < 3:
            return self
        norm = self.normal
        dx, dy, dz = norm.x * dist, norm.y * dist, norm.z * dist
        n = len(self.pts)
        top_pts = [Point3d(p.x + dx, p.y + dy, p.z + dz) for p in self.pts]

        top_face = Face(top_pts[::-1], material=self.material, parent_entities=self.parent)
        if self.parent:
            self.parent.faces.append(top_face)
            for i in range(n):
                p_cur = self.pts[i]
                p_nxt = self.pts[(i + 1) % n]
                q_cur = top_pts[i]
                q_nxt = top_pts[(i + 1) % n]
                side_f = Face([p_cur, p_nxt, q_nxt, q_cur], material=self.material, parent_entities=self.parent)
                self.parent.faces.append(side_f)
        return self


class BoundingBoxMock:
    def __init__(self):
        self.min = Point3d(0, 0, 0)
        self.max = Point3d(1, 1, 1)
        self.center = Point3d(0.5, 0.5, 0.5)
        self.width = 1.0
        self.height = 1.0
        self.depth = 1.0

    def corner(self, idx=0):
        return self.min if idx == 0 else self.max


class Group:
    def __init__(self, name="Group", layer=None, parent_entities=None):
        self.name = str(name or "Group")
        self.layer = layer
        self.parent = parent_entities
        self.entities = Entities(parent_group=self)
        self.attributes = {}

    def valid(self):
        return True

    def deleted(self):
        return False

    def transform_bang(self, *args):
        return self

    def move_bang(self, *args):
        if args and len(args) > 0:
            tr = args[0]
            if isinstance(tr, (list, tuple)) and len(tr) >= 3:
                dx, dy, dz = float(tr[0]), float(tr[1]), float(tr[2])
                for f in self.entities.faces:
                    for p in f.pts:
                        p.x += dx
                        p.y += dy
                        p.z += dz
                for g in self.entities.groups:
                    g.move_bang(args[0])
        return self

    def erase_bang(self, *args):
        if self.parent and hasattr(self.parent, 'groups'):
            try:
                self.parent.groups.remove(self)
            except Exception:
                pass

    def add_group(self, name="Group"):
        return self.entities.add_group(name=name)

    @property
    def bounds(self):
        return BoundingBoxMock()

    def set_attribute(self, dict_name, key, value):
        if dict_name not in self.attributes:
            self.attributes[dict_name] = {}
        self.attributes[dict_name][key] = value

    def get_attribute(self, dict_name, key, default=None):
        return self.attributes.get(dict_name, {}).get(key, default)


class Entities:
    def __init__(self, parent_group=None):
        self.parent_group = parent_group
        self.faces = RubyList()
        self.groups = RubyList()
        self.edges = RubyList()

    @property
    def entities(self):
        return self

    @property
    def find_faces(self):
        if not self.faces and self.edges:
            pts = [e.start for e in self.edges]
            f = Face(pts, parent_entities=self)
            self.faces.append(f)
        return self.faces

    def __getitem__(self, idx):
        all_e = list(self.faces) + list(self.groups) + list(self.edges)
        return all_e[idx]

    def __len__(self):
        return len(self.faces) + len(self.groups) + len(self.edges)

    def __call__(self):
        return self

    def __iter__(self):
        return iter(list(self.faces) + list(self.groups) + list(self.edges))

    def empty(self):
        return len(self.faces) == 0 and len(self.groups) == 0 and len(self.edges) == 0

    def clear(self):
        self.erase_entities()

    def erase_entities(self, *args):
        self.faces.clear()
        self.groups.clear()
        self.edges.clear()

    def add_group(self, name=None):
        g = Group(name=name or "Group", parent_entities=self)
        self.groups.append(g)
        return g

    def add_face(self, *args):
        flat = []
        def is_pt(it):
            return isinstance(it, (list, tuple, RubyList)) and 2 <= len(it) <= 4 and all(isinstance(x, (int, float)) for x in it)

        def _flatten(items):
            for it in items:
                if is_pt(it):
                    flat.append(Point3d(*it[:3]))
                elif isinstance(it, (list, tuple, RubyList)):
                    _flatten(it)
                elif hasattr(it, 'position'):
                    flat.append(it.position)
                elif hasattr(it, 'start'):
                    flat.append(it.start)
                else:
                    flat.append(it)
        _flatten(args)

        f = Face(flat, parent_entities=self)
        self.faces.append(f)
        if len(f.vertices) >= 2:
            for i in range(len(f.vertices)):
                p1 = f.vertices[i]
                p2 = f.vertices[(i + 1) % len(f.vertices)]
                e = Edge(p1, p2, parent_face=f)
                self.edges.append(e)
        return f

    def add_arc(self, center, normal, xaxis=None, radius=1.0, start_angle=0.0, end_angle=math.pi*0.5, num_segments=16):
        cx, cy, cz = float(center[0]), float(center[1]), float(center[2])
        rad = float(radius)
        segs = max(4, int(num_segments) if num_segments else 16)
        s_ang = float(start_angle)
        e_ang = float(end_angle)

        norm = Vector3d(*normal).normalize() if normal is not None else Vector3d(0, 0, 1)
        if xaxis is not None:
            u = Vector3d(*xaxis).normalize()
        elif abs(norm.z) < 0.9:
            u = norm.cross(Vector3d(0, 0, 1)).normalize()
        else:
            u = norm.cross(Vector3d(1, 0, 0)).normalize()
        v = norm.cross(u).normalize()

        arc_pts = []
        for i in range(segs + 1):
            t = i / float(segs)
            ang = s_ang + (e_ang - s_ang) * t
            ca = math.cos(ang) * rad
            sa = math.sin(ang) * rad
            px = cx + ca * u.x + sa * v.x
            py = cy + ca * u.y + sa * v.y
            pz = cz + ca * u.z + sa * v.z
            arc_pts.append(Point3d(px, py, pz))

        arc_edges = RubyList()
        for i in range(len(arc_pts) - 1):
            e = Edge(arc_pts[i], arc_pts[i + 1])
            self.edges.append(e)
            arc_edges.append(e)
        return arc_edges

    def add_edges(self, *args):
        created = RubyList()
        pts = args[0] if len(args) == 1 and isinstance(args[0], (list, tuple)) else args
        for i in range(len(pts) - 1):
            e = Edge(pts[i], pts[i+1])
            self.edges.append(e)
            created.append(e)
        return created

    def add_curve(self, *args):
        return self.add_edges(*args)

    def add_line(self, p1, p2):
        e = Edge(p1, p2)
        self.edges.append(e)
        return e

    def transform_entities(self, transform, entities_to_transform):
        return self

    def transform_by_vectors(self, entities_to_transform, vectors):
        return self

    def add_circle(self, center, normal, radius, num_segments=24):
        """Tạo các điểm tròn trên mặt phẳng với pháp tuyến vector bất kỳ."""
        cx, cy, cz = center[0], center[1], center[2]
        rad = float(radius)
        segs = max(8, int(num_segments))

        norm = Vector3d(*normal).normalize()
        if abs(norm.z) < 0.9:
            u = norm.cross(Vector3d(0, 0, 1)).normalize()
        else:
            u = norm.cross(Vector3d(1, 0, 0)).normalize()
        v = norm.cross(u).normalize()

        circle_pts = []
        for i in range(segs):
            ang = 2.0 * math.pi * i / segs
            ca = math.cos(ang) * rad
            sa = math.sin(ang) * rad
            px = cx + ca * u.x + sa * v.x
            py = cy + ca * u.y + sa * v.y
            pz = cz + ca * u.z + sa * v.z
            circle_pts.append(Point3d(px, py, pz))

        f = Face(circle_pts, parent_entities=self)
        self.faces.append(f)
        for i in range(len(circle_pts)):
            self.edges.append(Edge(circle_pts[i], circle_pts[(i + 1) % len(circle_pts)], parent_face=f))
        return circle_pts

    def add_cylinder(self, center, *args, **kwargs):
        if len(args) == 2:
            axis = Vector3d(0, 0, 1)
            radius = args[0]
            height = args[1]
        elif len(args) >= 3:
            axis = args[0]
            radius = args[1]
            height = args[2]
        else:
            axis = kwargs.get('axis', Vector3d(0, 0, 1))
            radius = kwargs.get('radius', 1.0)
            height = kwargs.get('height', 1.0)
        segments = kwargs.get('segments', 24)
        material = kwargs.get('material', None)

        cx, cy, cz = center[0], center[1], center[2]
        rad = float(radius)
        h = float(height)
        segs = max(8, int(segments))

        norm = Vector3d(*axis).normalize()
        if abs(norm.z) < 0.9:
            u = norm.cross(Vector3d(0, 0, 1)).normalize()
        else:
            u = norm.cross(Vector3d(1, 0, 0)).normalize()
        v = norm.cross(u).normalize()

        bot_pts = []
        top_pts = []
        for i in range(segs):
            ang = 2.0 * math.pi * i / segs
            ca = math.cos(ang) * rad
            sa = math.sin(ang) * rad
            bx = cx + ca * u.x + sa * v.x
            by = cy + ca * u.y + sa * v.y
            bz = cz + ca * u.z + sa * v.z
            bot_pts.append(Point3d(bx, by, bz))
            top_pts.append(Point3d(bx + norm.x * h, by + norm.y * h, bz + norm.z * h))

        new_faces = RubyList()
        f_bot = Face(bot_pts[::-1], material=material, parent_entities=self)
        f_top = Face(top_pts, material=material, parent_entities=self)
        self.faces.append(f_bot)
        self.faces.append(f_top)
        new_faces.append(f_bot)
        new_faces.append(f_top)

        for i in range(segs):
            b1 = bot_pts[i]
            b2 = bot_pts[(i + 1) % segs]
            t1 = top_pts[i]
            t2 = top_pts[(i + 1) % segs]
            f_side = Face([b1, b2, t2, t1], material=material, parent_entities=self)
            self.faces.append(f_side)
            new_faces.append(f_side)

        return new_faces

    def add_3d_text(self, string, *args, **kwargs):
        alignment = kwargs.get('alignment', 0)
        font = kwargs.get('font', 'Arial')
        is_bold = kwargs.get('is_bold', False)
        is_italic = kwargs.get('is_italic', False)
        letter_height = kwargs.get('letter_height', None)
        extrusion = kwargs.get('extrusion', None)
        material = kwargs.get('material', None)

        num_floats = []
        for i, a in enumerate(args):
            if isinstance(a, bool):
                pass
            elif isinstance(a, str):
                font = a
            elif isinstance(a, (int, float)):
                if i == 0 and a in (0, 1, 2) and letter_height is None:
                    alignment = a
                else:
                    num_floats.append(float(a))

        if len(num_floats) >= 2:
            h = num_floats[0]
            d = num_floats[1]
        elif len(num_floats) == 1:
            h = num_floats[0]
            d = 0.005
        else:
            h = float(letter_height) if letter_height else 0.1
            d = float(extrusion) if extrusion else 0.005

        if d <= 0:
            d = 0.005
        if h <= 0:
            h = 0.05

        w = max(0.02, len(str(string)) * h * 0.6)
        pts = [
            Point3d(0, 0, 0),
            Point3d(w, 0, 0),
            Point3d(w, d, 0),
            Point3d(0, d, 0)
        ]
        face = self.add_face(pts)
        if material:
            face.material = material
        face.pushpull(h)
        return face

    def grep(self, cls):
        if cls == Group:
            return RubyList(self.groups)
        if cls == Face:
            return RubyList(self.faces)
        if cls == Edge:
            return RubyList(self.edges)
        return RubyList()

    def to_a(self):
        return RubyList(list(self.faces) + list(self.groups) + list(self.edges))


class SelectionMock(RubyList):
    def add(self, *args):
        for a in args:
            self.append(a)

    def clear(self):
        super().clear()


class CameraMock:
    perspective = True

    def __init__(self, *a, **k):
        pass

    def set(self, *a, **k):
        pass

    @staticmethod
    def new(*a, **k):
        return CameraMock(*a, **k)


class ViewMock:
    camera = CameraMock()

    def zoom_extents(self):
        pass


class SketchupModel:
    def __init__(self):
        self.entities = Entities()
        self.materials = MaterialsCollection()
        self.layers = LayersCollection()
        self.attributes = {}
        self.selection = SelectionMock()

    @property
    def active_view(self):
        return ViewMock()

    @property
    def active_entities(self):
        return self.entities

    def start_operation(self, *args, **kwargs):
        pass

    def commit_operation(self):
        pass

    def abort_operation(self):
        pass

    def set_attribute(self, dict_name, key, value):
        if dict_name not in self.attributes:
            self.attributes[dict_name] = {}
        self.attributes[dict_name][key] = value

    def get_attribute(self, dict_name, key, default=None):
        return self.attributes.get(dict_name, {}).get(key, default)


class SketchupMock:
    Face = Face
    Group = Group
    ComponentInstance = Group
    Entities = Entities
    Material = Material
    Edge = Edge
    Vertex = Vertex
    Loop = Loop
    Color = Color
    Camera = CameraMock
    _active_model = None

    @classmethod
    def active_model(cls):
        if cls._active_model is None:
            cls._active_model = SketchupModel()
        return cls._active_model

    @classmethod
    def reset(cls):
        cls._active_model = SketchupModel()
        return cls._active_model


class FileMock:
    @staticmethod
    def join(*args):
        return os.path.join(*[str(a) for a in args])

    @staticmethod
    def directory(path):
        return os.path.isdir(str(path))

    @staticmethod
    def directory_p(path):
        return os.path.isdir(str(path))

    @staticmethod
    def exist(path):
        return os.path.exists(str(path))

    @staticmethod
    def exist_p(path):
        return os.path.exists(str(path))

    @staticmethod
    def basename(path, ext=None):
        base = os.path.basename(str(path))
        if ext and base.endswith(ext):
            base = base[:-len(ext)]
        return base

    @staticmethod
    def dirname(path):
        return os.path.dirname(str(path))

    @staticmethod
    def read(path, *args, **kwargs):
        with open(str(path), 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    @staticmethod
    def open(path, mode='r', *args, **kwargs):
        return open(str(path), mode, encoding='utf-8', errors='ignore')


class TransformationMock:
    def __init__(self, *args):
        pass

    def __mul__(self, other):
        return TransformationMock()

    def __rmul__(self, other):
        return TransformationMock()

    @staticmethod
    def translation(*args):
        return TransformationMock()

    @staticmethod
    def rotation(*args):
        return TransformationMock()

    @staticmethod
    def scaling(*args):
        return TransformationMock()

    @staticmethod
    def axes(*args):
        return TransformationMock()

    @staticmethod
    def interpolate(*args):
        return TransformationMock()

    @staticmethod
    def new(*args):
        return TransformationMock()


class GeomMock:
    Point3d = Point3d
    Vector3d = Vector3d
    Transformation = TransformationMock
    X_AXIS = Vector3d(1, 0, 0)
    Y_AXIS = Vector3d(0, 1, 0)
    Z_AXIS = Vector3d(0, 0, 1)
    ORIGIN = Point3d(0, 0, 0)


X_AXIS = Vector3d(1, 0, 0)
Y_AXIS = Vector3d(0, 1, 0)
Z_AXIS = Vector3d(0, 0, 1)
ORIGIN = Point3d(0, 0, 0)


class _RubyState:
    def __init__(self):
        self._data = {}

    def __getattr__(self, name):
        return self._data.get(name, None)

    def __setattr__(self, name, value):
        if name == '_data':
            super().__setattr__(name, value)
        else:
            if isinstance(value, list) and not isinstance(value, RubyList):
                value = RubyList(value)
            self._data[name] = value


class CSVMock:
    @staticmethod
    def open(*args, **kwargs):
        class _CSVWriter:
            def append(self, *a): pass
            def __enter__(self): return self
            def __exit__(self, *a): pass
        return _CSVWriter()


class MenuMock:
    def add_item(self, *a, **k):
        pass


class UIMock:
    @staticmethod
    def messagebox(msg, *args, **kwargs):
        pass

    @staticmethod
    def menu(*args, **kwargs):
        return MenuMock()


class RubyModule:
    def __init__(self, name="", scope=None):
        self._name = name
        self._scope = scope or {}

    def __getattr__(self, name):
        if name in self._scope:
            return self._scope[name]
        return None


# Standard geometry builder functions used by SketchUp scripts
def face_box(entities, x, y, z, sx, sy, sz, mat=None, name=None, layer_name=None, *extra_args):
    """Tạo khối hộp chữ nhật 6 mặt chuẩn xác."""
    target = entities.add_group(name=name) if name else entities
    target_ent = target.entities if hasattr(target, 'entities') else target

    pts = [
        Point3d(x, y, z), Point3d(x + sx, y, z), Point3d(x + sx, y + sy, z), Point3d(x, y + sy, z),
        Point3d(x, y, z + sz), Point3d(x + sx, y, z + sz), Point3d(x + sx, y + sy, z + sz), Point3d(x, y + sy, z + sz)
    ]
    target_ent.faces.append(Face([pts[0], pts[3], pts[2], pts[1]], material=mat, parent_entities=target_ent))
    target_ent.faces.append(Face([pts[4], pts[5], pts[6], pts[7]], material=mat, parent_entities=target_ent))
    target_ent.faces.append(Face([pts[0], pts[1], pts[5], pts[4]], material=mat, parent_entities=target_ent))
    target_ent.faces.append(Face([pts[1], pts[2], pts[6], pts[5]], material=mat, parent_entities=target_ent))
    target_ent.faces.append(Face([pts[2], pts[3], pts[7], pts[6]], material=mat, parent_entities=target_ent))
    target_ent.faces.append(Face([pts[3], pts[0], pts[4], pts[7]], material=mat, parent_entities=target_ent))
    return target


def box(entities, x, y, z, w, d, h, material=None, name=None, *extra_args):
    return face_box(entities, x, y, z, w, d, h, mat=material, name=name)


def add_box(entities, x, y, z, w, h, depth, mat=None, name=None, *extra_args):
    return face_box(entities, x, y, z, w, h, depth, mat=mat, name=name)


def group_box(parent, x, y, z, w, d, h, material=None, name=None, *extra_args):
    return face_box(parent, x, y, z, w, d, h, mat=material, name=name)


def add_round_bar(entities, p1, p2, diameter, mat=None, name=None, *extra_args):
    """Tạo thanh thép tròn giữa hai điểm p1 và p2."""
    v = p2 - p1
    L = v.length()
    if L < 1e-4:
        return None
    target = entities.add_group(name=name) if name else entities
    target_ent = target.entities if hasattr(target, 'entities') else target
    target_ent.add_cylinder(p1, v, diameter / 2.0, L, segments=12, material=mat)
    return target


def cyl(entities, center, radius, height, material=None, segments=24, *extra_args):
    target_ent = entities.entities if hasattr(entities, 'entities') else entities
    return target_ent.add_cylinder(center, [0, 0, 1], radius, height, segments=segments, material=material)


def cylinder(entities, center, axis, radius, height, material=None, segments=24, *extra_args):
    target_ent = entities.entities if hasattr(entities, 'entities') else entities
    return target_ent.add_cylinder(center, axis, radius, height, segments=segments, material=material)


# ==============================================================================
# 2. RUBY-TO-PYTHON TRANSPILER
# ==============================================================================

def clean_ruby_lexical(line):
    l = line
    # 1. Namespaces (::)
    l = l.replace('Geom::Point3d.new', 'Point3d')
    l = l.replace('Geom::Point3d', 'Point3d')
    l = l.replace('Geom::Vector3d.new', 'Vector3d')
    l = l.replace('Geom::Vector3d', 'Vector3d')
    l = l.replace('Sketchup::Color.new', 'Color')
    l = l.replace('Sketchup::Color', 'Color')
    l = l.replace('Sketchup::ComponentInstance', 'Group')
    l = l.replace('Sketchup::Entities', 'Entities')
    l = l.replace('Sketchup::Edge', 'Edge')
    l = l.replace('Sketchup::Face', 'Face')
    l = l.replace('Sketchup::Group', 'Group')
    l = l.replace('Sketchup::Material', 'Material')
    l = l.replace('Sketchup.active_model', 'Sketchup.active_model()')
    l = l.replace('Math::PI', 'math.pi')
    l = l.replace('::', '.')

    # Safe navigation &. -> .
    l = l.replace('&.', '.')

    # 2. Units & math conversions
    unit_target = r'((?:\d+(?:\.\d+)?)|(?:[a-zA-Z_][a-zA-Z0-9_]*(?:\[[^\]]+\])?))'
    l = re.sub(unit_target + r'\.degrees\b', r'(\1 * math.pi / 180.0)', l)
    l = re.sub(unit_target + r'\.mm\b', r'(\1 * 0.001)', l)
    l = re.sub(unit_target + r'\.cm\b', r'(\1 * 0.01)', l)
    l = re.sub(unit_target + r'\.m\b', r'(\1 * 1.0)', l)
    l = re.sub(unit_target + r'\.inch\b', r'(\1 * 0.0254)', l)

    # Clean enum assignments inside call arguments (e.g. TextAlignLeft = 0 -> 0)
    l = re.sub(r'\bTextAlign[A-Za-z]+\s*=\s*', '', l)

    # Math constants & array .max/.min
    l = l.replace('Math.PI', 'math.pi').replace('math.PI', 'math.pi')
    l = re.sub(r'\[([^\]]+)\]\.max\b', r'max([\1])', l)
    l = re.sub(r'\[([^\]]+)\]\.min\b', r'min([\1])', l)

    # 3. Ruby methods with !, ?
    l = l.replace('.reverse!', '.reverse_bang()')
    l = l.replace('.normalize!', '.normalize_bang()')
    l = re.sub(r'\.transform!\s*(\(.*?\))', r'.transform_bang\1', l)
    l = re.sub(r'\.transform!\s+([^;\n]+)', r'.transform_bang(\1)', l)
    l = l.replace('.transform!', '.transform_bang')

    l = re.sub(r'\.move!\s*(\(.*?\))', r'.move_bang\1', l)
    l = re.sub(r'\.move!\s+([^;\n]+)', r'.move_bang(\1)', l)
    l = l.replace('.move!', '.move_bang')
    l = l.replace('.erase!', '.erase_bang()')
    l = l.replace('.clear!', '.clear()')
    l = l.replace('.empty?', '.empty()')
    l = l.replace('.valid?', '.valid()')
    l = l.replace('.deleted?', '.deleted()')
    l = l.replace('.nil?', ' is None')
    l = l.replace('.zero?', ' == 0')

    # 4. Inline block methods: .select, .find_all, .reject, .map, .collect
    l = re.sub(r'\.select\s*\{\s*\|([^|]+)\|\s*(.*?)\s*\}', r'.select(lambda \1: \2)', l)
    l = re.sub(r'\.find_all\s*\{\s*\|([^|]+)\|\s*(.*?)\s*\}', r'.select(lambda \1: \2)', l)
    l = re.sub(r'\.reject\s*\{\s*\|([^|]+)\|\s*(.*?)\s*\}', r'.reject(lambda \1: \2)', l)
    l = re.sub(r'\.map\s*\{\s*\|([^|]+)\|\s*(.*?)\s*\}', r'.map(lambda \1: \2)', l)
    l = re.sub(r'\.collect\s*\{\s*\|([^|]+)\|\s*(.*?)\s*\}', r'.collect(lambda \1: \2)', l)
    l = l.replace('.floor', '.__floor__()')
    l = l.replace('.ceil', '.__ceil__()')
    l = re.sub(r'\.round\b(?!\()', '.__round__()', l)
    l = l.replace('.round(', '.__round__(')
    l = l.replace('.abs', '.__abs__()')
    l = re.sub(r'(\b[a-zA-Z0-9_.]+)\.include\?\s*\((.*?)\)', r'(\2 in \1)', l)
    l = re.sub(r'\.normalize\b(?!\()', '.normalize()', l)
    l = re.sub(r'(\b[a-zA-Z0-9_]+)\.call\(', r'\1(', l)
    l = re.sub(r'(\b\w+)\.even\?', r'(\1 % 2 == 0)', l)
    l = re.sub(r'(\b\w+)\.odd\?', r'(\1 % 2 != 0)', l)
    l = re.sub(r'(\b\w+)\.is_a\?\s*\((.*?)\)', r'isinstance(\1, \2)', l)
    l = re.sub(r'(\b\w+)\.is_a\?\s+([A-Za-z0-9_]+)', r'isinstance(\1, \2)', l)
    l = re.sub(r'(\b\w+)\.respond_to\?\s*\(:?([A-Za-z0-9_]+)=?\)', r'hasattr(\1, "\2")', l)
    l = re.sub(r'\.add_group\b(?!\()', '.add_group()', l)
    l = re.sub(r'\.active_model\b(?!\()', '.active_model()', l)
    l = re.sub(r'\.commit_operation\b(?!\()', '.commit_operation()', l)
    l = re.sub(r'\.abort_operation\b(?!\()', '.abort_operation()', l)
    l = re.sub(r'\.zoom_extents\b(?!\()', '.zoom_extents()', l)
    l = re.sub(r'\.clear\b(?!\()', '.clear()', l)
    l = re.sub(r'\.empty\b(?!\()', '.empty()', l)
    l = re.sub(r'\.to_a\b(?!\()', '.to_a()', l)
    l = re.sub(r'(\b\w+positions|\b\w+list|\b\w+arr|\b\w+items|\b\w+pts|\b\w+segments)\.length\b', r'len(\1)', l)
    tif_len = check_trailing_if(l)
    if tif_len and '.length' in tif_len[0]:
        l = f"if {tif_len[1]}: {tif_len[0]}"
    tun_len = check_trailing_unless(l)
    if tun_len and '.length' in tun_len[0]:
        l = f"if not ({tun_len[1]}): {tun_len[0]}"
    l = re.sub(r'(\b[a-zA-Z0-9_.]+)\.length\s*(?<![=<>!])=(?!=)\s*(.*)$', r'\1.set_length(\2)', l)
    l = re.sub(r'\.length\b(?!\s*[\+\-\*\/\%]?=)(?!\()', '.length()', l)
    l = l.replace('.dup', '.copy()')
    l = l.replace('.chars', '')
    l = re.sub(r'^\s*([A-Za-z0-9_]+)\s*=\s*([^,]+),\s*$', r'\2,', l)
    l = re.sub(r'\.clone\b(?!\()', '.clone()', l)
    l = l.replace('.erase!', '.erase()')
    l = re.sub(r'(\b[a-zA-Z0-9_.]+)\.to_mm\b', r'(\1 * 1000.0)', l)
    l = re.sub(r'(\b[a-zA-Z0-9_.]+)\.to_m\b', r'(\1 * 1.0)', l)
    l = re.sub(r'(\b[a-zA-Z0-9_.]+)\.to_cm\b', r'(\1 * 100.0)', l)
    l = l.replace('.to_f', '')
    l = l.replace('.to_s', '')
    l = l.replace('.to_i', '.__int__()')

    # String interpolation & gsub
    l = re.sub(r'\.gsub\(/\\s\+?/, (.*?)\)', r".replace(' ', \1)", l)
    l = re.sub(r'#\{([^}]+)\}', r'{\1}', l)
    if '"{' in l and not l.strip().startswith('f"') and not l.strip().startswith("f'"):
        l = re.sub(r'(?<![a-zA-Z0-9_])"([^"]*\{[^"]*\}[^"]*)"', r'f"\1"', l)

    # 4. Booleans and nil
    l = re.sub(r'\bnil\b', 'None', l)
    l = re.sub(r'\btrue\b', 'True', l)
    l = re.sub(r'\bfalse\b', 'False', l)

    # 4b. Instance variables @var -> _RB_STATE.var
    l = re.sub(r'@([A-Za-z0-9_]+)', r'_RB_STATE.\1', l)

    # 4c. Trailing rescue -> strip
    l = re.sub(r'\s+rescue\s+(None|nil|false|true|\d+|"[^"]*"|\'[^\']*\')\s*$', '', l)

    # 5. Logic
    l = l.replace('||', ' or ').replace('&&', ' and ')

    # 5b. Convert Ruby predicate method calls (e.g., File.directory?(desktop)) before ternary ? :
    l = re.sub(r'(\b[a-zA-Z0-9_]+)\?(?=\()', r'\1_p', l)
    l = re.sub(r'(\b[a-zA-Z0-9_]+)\?(?=\.)', r'\1_p', l)

    # 6. Robust Ternary Operator handling (all positions: assignment, args, arrays, parens)
    if '?' in l and ':' in l:
        def _repl_ternary(m):
            full_cond = m.group(1).strip()
            v_true = m.group(2).strip()
            v_false = m.group(3).strip()
            m_assign = re.match(r'^(.*?)(?<![=!<>])=(?!=)(.*)$', full_cond)
            if m_assign:
                prefix = m_assign.group(1) + '='
                cond = m_assign.group(2).strip()
                return f'{prefix} ({v_true} if {cond} else {v_false})'
            return f'({v_true} if {full_cond} else {v_false})'

        pat_ternary = re.compile(r'([^,()\[\]]+?)\s*\?\s*([^,()\[\]:]+?)\s*:\s*([^,()\[\]]+)')
        for _ in range(5):
            new_l = pat_ternary.sub(_repl_ternary, l)
            if new_l == l:
                break
            l = new_l

    # 6b. Any remaining methods ending with ? -> _p (e.g. parallel? -> parallel_p)
    l = re.sub(r'(\b[a-zA-Z0-9_]+)\?', r'\1_p', l)

    # 7. Ruby Symbols (:front, :side, :x, :y) - must start with letter or underscore
    l = re.sub(r'(?<!:):([A-Za-z_][A-Za-z0-9_]*)', r"'\1'", l)

    # 8. Ruby array append <<
    def _replace_append(m):
        target = m.group(1)
        expr = m.group(2).strip()
        trail = m.group(3) or ""
        return f"{target}.append({expr}){trail}"

    l = re.sub(r'\b([a-zA-Z0-9_.]+)\s*<<\s*([^;{}\n]+?)(\s*[;}]\s*.*)?$', _replace_append, l)

    # 9. Inline .map { |var| expr } -> [expr for var in target]
    map_m = re.search(r'(.*?)\.map\s*\{\s*\|(.*?)\|\s*(.*?)\s*\}', l)
    if map_m:
        full_prefix = map_m.group(1)
        var = map_m.group(2).strip()
        body = map_m.group(3).strip()
        trail = l[map_m.end():]
        assign_m = re.match(r'^(.*?[^=><!]=)\s*(.*)$', full_prefix)
        if assign_m:
            assign_part = assign_m.group(1)
            arr_target = assign_m.group(2).strip()
            l = f"{assign_part} [{body} for {var} in {arr_target}]{trail}"
        else:
            l = f"[{body} for {var} in {full_prefix.strip()}]{trail}"

    # Handle .uniq on list or RubyList
    l = re.sub(r'(\[[^\]]+\])\.uniq\b(?:\(\))?', r'RubyList(\1).uniq()', l)

    # 9b. Hash rockets => to :
    l = re.sub(r'\s*=>\s*', ': ', l)

    # 10. Array find: arr.find { |x| cond } -> next((x for x in arr if cond), None)
    find_m = re.search(r'(\w+)\.find\s*\{\s*\|(\w+)\|\s*(.*?)\s*\}', l)
    if find_m:
        arr_nm = find_m.group(1)
        item_nm = find_m.group(2)
        cond_expr = find_m.group(3)
        l = l[:find_m.start()] + f"next(({item_nm} for {item_nm} in {arr_nm} if {cond_expr}), None)" + l[find_m.end():]

    # 11. puts -> print(...)
    puts_m = re.match(r'^puts\s+(.*)$', l.strip())
    if puts_m:
        val = puts_m.group(1).strip()
        if not (val.startswith('(') and val.endswith(')')):
            l = f"print({val})"

    return l


def check_trailing_if(l):
    if l.startswith(('if ', 'unless ', 'def ', 'while ', 'for ', 'elif ', 'else:')):
        return None
    matches = [m.start() for m in re.finditer(r'\s+if\s+', l)]
    for idx in reversed(matches):
        prefix = l[:idx]
        if prefix.count('(') == prefix.count(')') and prefix.count('[') == prefix.count(']'):
            action = l[:idx].strip()
            cond = l[idx + 4:].strip()
            if action and cond and not cond.endswith(':'):
                return (action, cond)
    return None


def check_trailing_unless(l):
    if l.startswith(('if ', 'unless ', 'def ', 'while ', 'for ', 'elif ', 'else:')):
        return None
    matches = [m.start() for m in re.finditer(r'\s+unless\s+', l)]
    for idx in reversed(matches):
        prefix = l[:idx]
        if prefix.count('(') == prefix.count(')') and prefix.count('[') == prefix.count(']'):
            action = l[:idx].strip()
            cond = l[idx + 8:].strip()
            if action and cond and not cond.endswith(':'):
                return (action, cond)
    return None


def strip_ruby_comment(line):
    in_s = False
    in_d = False
    for i, ch in enumerate(line):
        if ch == "'" and not in_d:
            in_s = not in_s
        elif ch == '"' and not in_s:
            in_d = not in_d
        elif ch == '#' and not in_s and not in_d:
            return line[:i].strip()
    return line.strip()


def transpile_ternary(line):
    if '?' not in line or ':' not in line:
        return line
    for _ in range(8):
        found_q = []
        depth = 0
        in_s = False
        in_d = False
        for i, ch in enumerate(line):
            if ch == "'" and not in_d: in_s = not in_s
            elif ch == '"' and not in_s: in_d = not in_d
            elif not in_s and not in_d:
                if ch in '([{': depth += 1
                elif ch in ')]}': depth -= 1
                elif ch == '?': found_q.append((i, depth))
        if not found_q: break

        replaced = False
        for q_idx, q_depth in reversed(found_q):
            depth = q_depth
            c_idx = -1
            in_s = False
            in_d = False
            for j in range(q_idx + 1, len(line)):
                ch = line[j]
                if ch == "'" and not in_d: in_s = not in_s
                elif ch == '"' and not in_s: in_d = not in_d
                elif not in_s and not in_d:
                    if ch in '([{': depth += 1
                    elif ch in ')]}': depth -= 1
                    elif ch == ':' and depth == q_depth:
                        c_idx = j
                        break
                    elif ch == '?' and depth == q_depth:
                        break
            if c_idx != -1:
                depth = q_depth
                cond_start = 0
                for k in range(q_idx - 1, -1, -1):
                    ch = line[k]
                    if ch in '([{':
                        depth -= 1
                        if depth < q_depth: cond_start = k + 1; break
                    elif ch in ')]}':
                        depth += 1
                    elif depth == q_depth:
                        if ch in ',;': cond_start = k + 1; break
                        if ch == '=':
                            prev_ch = line[k-1] if k > 0 else ''
                            next_ch = line[k+1] if k+1 < len(line) else ''
                            if prev_ch not in ('=', '!', '<', '>') and next_ch != '=':
                                cond_start = k + 1; break
                depth = q_depth
                val_end = len(line)
                for k in range(c_idx + 1, len(line)):
                    ch = line[k]
                    if ch in '([{': depth += 1
                    elif ch in ')]}':
                        depth -= 1
                        if depth < q_depth: val_end = k; break
                    elif depth == q_depth and ch in ',;': val_end = k; break

                cond_str = line[cond_start:q_idx].strip()
                val_t_str = line[q_idx+1:c_idx].strip()
                val_f_str = line[c_idx+1:val_end].strip()

                repl = f"({val_t_str} if ({cond_str}) else {val_f_str})"
                line = line[:cond_start] + repl + line[val_end:]
                replaced = True
                break
        if not replaced: break
    return line


def pre_sanitize_ruby_code(rb_code):
    lines = rb_code.splitlines()
    clean_lines = []
    case_stack = []

    for line in lines:
        l = line
        stripped = l.strip()

        # Handle case / when / else / end
        m_case = re.match(r'^case\s+(.*)$', stripped)
        if m_case:
            target_expr = m_case.group(1).strip()
            indent = " " * (len(l) - len(l.lstrip()))
            clean_lines.append(f"{indent}_case_val = {target_expr}")
            case_stack.append(('case', indent))
            continue

        if case_stack:
            m_when = re.match(r'^when\s+(.*)$', stripped)
            if m_when:
                vals = [v.strip() for v in m_when.group(1).split(',')]
                base_indent = case_stack[-1][1]
                state = case_stack[-1][0]
                cond = " or ".join(f"_case_val == {v}" for v in vals)
                if state == 'case':
                    clean_lines.append(f"{base_indent}if {cond}:")
                    case_stack[-1] = ('case_when', base_indent)
                else:
                    clean_lines.append(f"{base_indent}elif {cond}:")
                continue

            if stripped.startswith('else') and case_stack[-1][0] == 'case_when':
                base_indent = case_stack[-1][1]
                clean_lines.append(f"{base_indent}else:")
                continue

            if stripped == 'end' and case_stack[-1][0] in ('case', 'case_when'):
                st = case_stack.pop()
                if st[0] == 'case_when':
                    clean_lines.append(f"{st[1]}end")
                continue

        # Strip self.call() when at top/module level
        l = re.sub(r'\bself\.([A-Za-z0-9_]+)\(', r'\1(', l)

        # Fix .delete('#') -> .replace('#', '')
        l = re.sub(r'([a-zA-Z0-9_]+)\.delete\((["\'][^"\']*["\'])\)', r'\1.replace(\2, "")', l)

        # Raise ArgumentError, 'msg' -> raise ValueError('msg')
        m_raise = re.match(r'^(.*?\braise\s+[A-Za-z0-9_]+)\s*,\s*(.*)$', l)
        if m_raise:
            l = f"{m_raise.group(1)}({m_raise.group(2)})"

        # Fix add_3d_text named arguments inside calls everywhere:
        l = re.sub(r'\b(?:TextAlignLeft|TextAlignCenter|TextAlignRight)\s*=\s*', '', l)
        l = re.sub(r'\b(?:Font|Bold|Italic)\s*=\s*', '', l)

        # Fix string .each_char -> for char in str:
        l = re.sub(r'\.each_char\b', '', l)

        # Fix hex[0..1].to_i(16) -> int(hex[0:2], 16)
        l = re.sub(r'([a-zA-Z0-9_]+)\[(\d+)\.\.(\d+)\]\.to_i\s*\(\s*16\s*\)', lambda m: f"int({m.group(1)}[{m.group(2)}:{int(m.group(3))+1}], 16)", l)

        # Fix Ruby range slices: [0..1] -> [0:2], [2..3] -> [2:4], [4..5] -> [4:6], [1..-1] -> [1:]
        l = re.sub(r'\[\s*(\d+)\s*\.\.\s*-1\s*\]', r'[\1:]', l)
        l = re.sub(r'\[\s*(\d+)\s*\.\.\s*(\d+)\s*\]', lambda m: f"[{m.group(1)}:{int(m.group(2))+1}]", l)

        # Fix .map(&:prop)
        l = re.sub(r'\.map\(&[\':]?([A-Za-z0-9_]+)[\']?\)', r'.map { |x| x.\1 }', l)

        # Fix .all? { |var| cond } and .any? { |var| cond }
        l = re.sub(r'([a-zA-Z0-9_.]+)\.all\?\s*\{\s*\|(\w+)\|\s*(.*?)\s*\}', r'all([\3 for \2 in \1])', l)
        l = re.sub(r'([a-zA-Z0-9_.]+)\.any\?\s*\{\s*\|(\w+)\|\s*(.*?)\s*\}', r'any([\3 for \2 in \1])', l)

        # Fix .grep(...) { |var| body } BEFORE m_append_if
        m_grep_inline = re.match(r'^(.*?[a-zA-Z0-9_.]+)\.grep\((.*?)\)\s*\{\s*\|(.*?)\|\s*(.*?)(?:\s*\})?$', stripped)
        if m_grep_inline:
            recv = m_grep_inline.group(1)
            target_cls = m_grep_inline.group(2)
            var = m_grep_inline.group(3)
            body = m_grep_inline.group(4)
            indent = " " * (len(l) - len(l.lstrip()))
            clean_lines.append(f"{indent}for {var} in {recv}.grep({target_cls}):")
            m_a_if = re.match(r'^(.*?)\b([a-zA-Z0-9_.]+)\s*<<\s*([^;{}]+?)\s+if\s+(.*?)(?:\s*\})?$', body.strip())
            if m_a_if:
                clean_lines.append(f"{indent}    if {m_a_if.group(4).strip()}: {m_a_if.group(2)}.append({m_a_if.group(3).strip()})")
            else:
                m_b_if = re.match(r'^(.*?)\s+if\s+(.*?)(?:\s*\})?$', body.strip())
                if m_b_if:
                    clean_lines.append(f"{indent}    if {m_b_if.group(2)}: {m_b_if.group(1)}")
                else:
                    clean_lines.append(f"{indent}    {body}")
            continue

        # Fix target << var if cond
        m_append_if = re.match(r'^(.*?)\b([a-zA-Z0-9_.]+)\s*<<\s*([^;{}]+?)\s+if\s+(.*?)(?:\s*\})?$', l)
        if m_append_if:
            pre = m_append_if.group(1)
            target = m_append_if.group(2)
            val = m_append_if.group(3).strip()
            cond = m_append_if.group(4).strip()
            indent = " " * (len(l) - len(l.lstrip()))
            clean_lines.append(f"{indent}if {cond}: {target}.append({val})")
            continue

        # Fix method calls without parens (skip multiline calls that have open parens)
        m_call = re.match(r'^((?:[a-zA-Z0-9_.]+\s*=\s*)?[a-zA-Z0-9_.]+\.(?:move!|transform!|pushpull|add_face|add_group|add_line|add_cylinder|add_circle|set_attribute))\s+([^(=+\-*/].*)$', stripped)
        if m_call and not stripped.endswith(('do', '{')):
            arg_part = m_call.group(2).strip()
            if arg_part.count('(') == arg_part.count(')') and not (arg_part.startswith('(') and arg_part.endswith(')')):
                indent = " " * (len(l) - len(l.lstrip()))
                l = f"{indent}{m_call.group(1)}({arg_part})"

        # Fix .downto(limit) do |i|
        m_downto = re.match(r'^\s*\(?(.*?)\)?\.downto\((.*?)\)\s+do\s*\|(.*?)\|\s*$', l)
        if m_downto:
            s_from = m_downto.group(1).strip()
            s_to = m_downto.group(2).strip()
            s_var = m_downto.group(3).strip()
            indent = " " * (len(l) - len(l.lstrip()))
            l = f"{indent}for {s_var} in range(int({s_from}), int({s_to}) - 1, -1):"

        # Fix .tap { |m| m.color = ... }
        l = re.sub(r'\.tap\s*\{\s*\|(\w+)\|\s*\1\.color\s*=\s*([^}]+)\}', r'', l)

        # Fix hash literal keys { char: "D", width: 100 } -> { 'char': "D", 'width': 100 }
        if '{' in l and '}' in l and ':' in l:
            def _repl_hash_keys(m):
                content = m.group(1)
                if content.strip().startswith('|'):
                    return '{' + content + '}'
                c_fixed = re.sub(r'(?<!:)\b([a-zA-Z0-9_]+):(?!=|:)', r"'\1':", content)
                return '{' + c_fixed + '}'
            l = re.sub(r'\{([^{}]+)\}', _repl_hash_keys, l)

        # Fix .step(x).map { |a| ... }
        m_step_map = re.search(r'\((\d+)\.\.(\d+)\)\.step\((\d+)\)\.map\s*\{\s*\|(\w+)\|\s*(.*?)\s*\}', l)
        if m_step_map:
            s_from = m_step_map.group(1)
            s_to = m_step_map.group(2)
            s_step = m_step_map.group(3)
            s_var = m_step_map.group(4)
            s_expr = m_step_map.group(5)
            repl = f"[{s_expr} for {s_var} in range({s_from}, {int(s_to)}+1, {s_step})]"
            l = l[:m_step_map.start()] + repl + l[m_step_map.end():]

        # Fix trailing if with comment
        m_trail_comment = re.search(r'^(.*?)\s+if\s+(.*?)\s*(#.*)$', l)
        if m_trail_comment and not l.strip().startswith(('if ', 'unless ', 'def ', 'while ', 'for ')):
            action = m_trail_comment.group(1).strip()
            cond = m_trail_comment.group(2).strip()
            comment = m_trail_comment.group(3).strip()
            indent = " " * (len(l) - len(l.lstrip()))
            l = f"{indent}if {cond}: {action}  {comment}"

        # Fix (0..wave_count*2).each do |i| or (0...led_count).each do |i|
        m_rng_each = re.match(r'^\s*\((\d+)\s*(\.\.\.?)\s*(.*?)\)\.each\s+do\s*\|(.*?)\|\s*$', l)
        if m_rng_each:
            r_start = m_rng_each.group(1)
            dots = m_rng_each.group(2)
            r_end = m_rng_each.group(3).strip()
            r_var = m_rng_each.group(4).strip()
            indent = " " * (len(l) - len(l.lstrip()))
            if dots == '...':
                l = f"{indent}for {r_var} in range({r_start}, int({r_end})):"
            else:
                l = f"{indent}for {r_var} in range({r_start}, int({r_end}) + 1):"

        # Fix for i in (1..(width/500)):
        m_for_rng = re.match(r'^\s*for\s+(\w+)\s+in\s+\(?(\d+)\s*(\.\.\.?)\s*(.*?)\)?:\s*$', l)
        if m_for_rng:
            r_var = m_for_rng.group(1)
            r_start = m_for_rng.group(2)
            dots = m_for_rng.group(3)
            r_end = m_for_rng.group(4).rstrip(')').strip()
            indent = " " * (len(l) - len(l.lstrip()))
            if dots == '...':
                l = f"{indent}for {r_var} in range({r_start}, int({r_end})):"
            else:
                l = f"{indent}for {r_var} in range({r_start}, int({r_end}) + 1):"

        # Fix string .size
        l = re.sub(r'(\b[a-zA-Z0-9_.[\]]+)\.size\b', r'len(\1)', l)

        # Fix .map(lambda var: expr) and .map{|var| expr} on lists
        l = re.sub(r'([a-zA-Z0-9_.[\]]+)\.map\s*\(\s*lambda\s+(\w+)\s*:\s*(.*?)\s*\)', r'[\3 for \2 in \1]', l)
        l = re.sub(r'([a-zA-Z0-9_.[\]]+)\.map\s*\{\s*\|(\w+)\|\s*(.*?)\s*\}', r'[\3 for \2 in \1]', l)

        # Fix .reverse! -> .reverse_bang() and .reverse -> RubyList(...).reverse()
        l = re.sub(r'\.reverse!\b', r'.reverse_bang()', l)
        l = re.sub(r'(\[[^\]]+\])\.reverse\b(?:\(\))?', r'RubyList(\1).reverse()', l)
        l = re.sub(r'([a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)*)\.reverse\b(?!\s*[!])(?:\(\))?', r'RubyList(\1).reverse()', l)

        # Fix [ ... ].uniq -> RubyList([ ... ]).uniq()
        l = re.sub(r'(\[[^\]]+\])\.uniq\b(?:\(\))?', r'RubyList(\1).uniq()', l)

        # Fix float indexing arr[i/2] -> arr[int(i/2)]
        l = re.sub(r'\[\s*([a-zA-Z0-9_+\-*%]+)\s*/\s*([a-zA-Z0-9_+\-*%]+)\s*\]', r'[int(\1 / \2)]', l)

        # Fix pt.x, pt.y, pt.z -> pt[0], pt[1], pt[2] for points/lists
        l = re.sub(r'(\bp[12]|\bpt)\.x\b', r'\1[0]', l)
        l = re.sub(r'(\bp[12]|\bpt)\.y\b', r'\1[1]', l)
        l = re.sub(r'(\bp[12]|\bpt)\.z\b', r'\1[2]', l)

        # Fix ternary operators
        l = transpile_ternary(l)

        clean_lines.append(l)

    return "\n".join(clean_lines)


def transpile_ruby_to_python(rb_code):
    """
    Chuyển đổi cú pháp SketchUp Ruby sang Python script tương thích với Mock Engine.
    """
    rb_code = pre_sanitize_ruby_code(rb_code)
    raw_lines = rb_code.splitlines()
    output_lines = [
        "# --- Auto-Transpiled from SketchUp Ruby ---",
        "import math, os",
        "Math = math",
        "ENV = os.environ",
        "File = FileMock",
        "CSV = CSVMock",
        "TextAlignLeft = 0",
        "TextAlignCenter = 1",
        "TextAlignRight = 2",
        "model = Sketchup.active_model()",
        "entities = model.entities",
        "materials = model.materials",
        "layers = model.layers",
        "_RB_STATE = _RubyState()",
        "X_AXIS = Vector3d(1, 0, 0)",
        "Y_AXIS = Vector3d(0, 1, 0)",
        "Z_AXIS = Vector3d(0, 0, 1)",
        "ORIGIN = Point3d(0, 0, 0)",
        "Z_UP = Vector3d(0, 0, 1)",
        ""
    ]

    # Pre-process: Expand one-line defs like "def mat(name); @materials[name]; end"
    expanded_raw = []
    for line in raw_lines:
        s = line.strip()
        m_inline_def = re.match(r'^(\s*def\s+[A-Za-z0-9_!?.]+(?:\(.*?\)|[^\;]*?))\s*;\s*(.*?)\s*(?:;\s*)?end\s*$', s)
        if m_inline_def:
            expanded_raw.append(m_inline_def.group(1))
            for sub_s in m_inline_def.group(2).split(';'):
                if sub_s.strip():
                    expanded_raw.append("    " + sub_s.strip())
            expanded_raw.append("end")
        else:
            expanded_raw.append(line)
    raw_lines = expanded_raw

    joined_lines = []
    i = 0
    while i < len(raw_lines):
        line = raw_lines[i]
        stripped = line.strip()

        # Check pure comment line FIRST
        if stripped.startswith('#'):
            joined_lines.append(line)
            i += 1
            continue

        s_code = strip_ruby_comment(stripped)
        if s_code.endswith('\\'):
            s_code = s_code[:-1].rstrip()

        # Multiline def
        if s_code.startswith('def ') and '(' in s_code and s_code.count('(') > s_code.count(')'):
            full_def = s_code
            i += 1
            while i < len(raw_lines) and full_def.count('(') > full_def.count(')'):
                full_def += " " + strip_ruby_comment(raw_lines[i]).rstrip('\\').rstrip()
                i += 1
            joined_lines.append(full_def)
            continue

        # Multiline array/hash with .each or .times at the end
        if ('.each' in s_code or '.times' in s_code) and (
            s_code.count(']') > s_code.count('[') or s_code.count('}') > s_code.count('{')
        ):
            acc = [s_code]
            needed_b = s_code.count(']') - s_code.count('[')
            needed_c = s_code.count('}') - s_code.count('{')
            while joined_lines and (needed_b > 0 or needed_c > 0):
                prev = joined_lines.pop()
                acc.insert(0, strip_ruby_comment(prev).rstrip('\\').rstrip())
                needed_b -= (prev.count('[') - prev.count(']'))
                needed_c -= (prev.count('{') - prev.count('}'))
            joined_lines.append(" ".join(acc))
            i += 1
            continue

        # Multiline expression with unclosed (, [ or {
        if not s_code.startswith(('def ', 'class ', 'module ')) and (
            s_code.count('(') > s_code.count(')') or 
            s_code.count('[') > s_code.count(']') or 
            s_code.count('{') > s_code.count('}')
        ):
            acc = [s_code]
            open_p = s_code.count('(') - s_code.count(')')
            open_b = s_code.count('[') - s_code.count(']')
            open_c = s_code.count('{') - s_code.count('}')
            i += 1
            while i < len(raw_lines) and (open_p > 0 or open_b > 0 or open_c > 0):
                nxt = raw_lines[i]
                nxt_s = nxt.strip()
                if nxt_s.startswith(('def ', 'class ', 'module ', 'end')):
                    break
                if nxt_s.startswith('#'):
                    i += 1
                    continue
                nxt_code = strip_ruby_comment(nxt_s).rstrip('\\').rstrip()
                if nxt_code:
                    acc.append(nxt_code)
                    open_p += nxt_code.count('(') - nxt_code.count(')')
                    open_b += nxt_code.count('[') - nxt_code.count(']')
                    open_c += nxt_code.count('{') - nxt_code.count('}')
                i += 1
            joined_lines.append(" ".join(acc))
            continue

        # Multiline assignment or continuation operator
        if s_code.endswith(('=', '+=', '-=', '*=', '/=', '+', '-', '*', '/', ',', '||', '&&', ' and', ' or')):
            acc = [s_code]
            while acc[-1].endswith(('=', '+=', '-=', '*=', '/=', '+', '-', '*', '/', ',', '||', '&&', ' and', ' or')):
                i += 1
                while i < len(raw_lines) and not strip_ruby_comment(raw_lines[i].strip()):
                    i += 1
                if i < len(raw_lines):
                    nxt_code = strip_ruby_comment(raw_lines[i].strip()).rstrip('\\').rstrip()
                    if nxt_code:
                        acc.append(nxt_code)
                else:
                    break
            joined_lines.append(" ".join(acc))
            i += 1
            continue

        joined_lines.append(line)
        i += 1
    raw_lines = joined_lines

    zero_arg_funcs = set()
    for rl in raw_lines:
        m_def = re.match(r'^\s*def\s+([A-Za-z0-9_.]+)(\s*\(\s*\)|\s*$)', rl)
        if m_def:
            fn_name = m_def.group(1).split('.')[-1]
            if len(fn_name) > 1 and fn_name not in ('x', 'y', 'z', 'm', 'p', 'w', 'h', 'd', 'r', 'g', 'b', 'a'):
                zero_arg_funcs.add(fn_name)

    block_stack = []
    indent_step = "    "
    in_rescue = False
    has_begin = False
    in_menu_block = False

    for line in raw_lines:
        stripped = line.strip()

        if not stripped:
            output_lines.append("")
            continue

        if stripped.startswith('#'):
            indent_level = len(block_stack)
            output_lines.append(indent_step * indent_level + stripped)
            continue

        if stripped.startswith('require ') or stripped == 'extend self' or 'frozen_string_literal' in stripped:
            indent_level = len(block_stack)
            output_lines.append(indent_step * indent_level + f"# {stripped}")
            continue

        # Handle Rescue
        if stripped.startswith('rescue'):
            in_rescue = True
            indent_level = len(block_stack)
            output_lines.append(indent_step * indent_level + f"# {stripped}")
            continue

        # Handle 'end' keyword
        if stripped == 'end':
            if in_rescue:
                in_rescue = False
                if has_begin:
                    has_begin = False
                    indent_level = len(block_stack)
                    output_lines.append(indent_step * indent_level + "# end (begin rescue)")
                elif block_stack:
                    popped = block_stack.pop()
                    indent_level = len(block_stack)
                    output_lines.append(indent_step * indent_level + f"# end ({popped} rescue)")
                else:
                    output_lines.append("# end (rescue)")
                continue

            if block_stack:
                popped = block_stack.pop()
                if popped.startswith('map:'):
                    map_target = popped.split(':', 1)[1]
                    idx = len(output_lines) - 1
                    while idx >= 0:
                        prev_l = output_lines[idx].strip()
                        if prev_l and not prev_l.startswith('#'):
                            indent_len = len(output_lines[idx]) - len(output_lines[idx].lstrip())
                            output_lines[idx] = output_lines[idx][:indent_len] + f"{map_target}.append({prev_l})"
                            break
                        idx -= 1
                    indent_level = len(block_stack)
                    output_lines.append(indent_step * indent_level + f"# end (map {map_target})")
                    continue
                if popped == 'def':
                    # Only insert implicit return if the last statement in the def body is a standalone expression
                    idx = len(output_lines) - 1
                    while idx >= 0:
                        prev_line = output_lines[idx]
                        prev_l = prev_line.strip()
                        if prev_l.startswith('# end ('):
                            # The function ended right after a closed inner block (like a loop or if)
                            break
                        if prev_l and not prev_l.startswith('#'):
                            indent_len = len(prev_line) - len(prev_line.lstrip())
                            # Must be directly in def body (indent_len == (len(block_stack) + 1) * 4)
                            if indent_len == (len(block_stack) + 1) * len(indent_step):
                                if not prev_l.startswith(('return ', 'def ', 'if ', 'while ', 'for ', 'elif ', 'else:', 'print(', 'with ')):
                                    has_assign = False
                                    for eq_tok in ('=', '+=', '-=', '*=', '/='):
                                        if eq_tok in prev_l:
                                            pos = prev_l.find(eq_tok)
                                            b = prev_l[pos-1:pos] if pos > 0 else ''
                                            a = prev_l[pos+len(eq_tok):pos+len(eq_tok)+1]
                                            if b not in ('<', '>', '!', '=') and a != '=':
                                                has_assign = True
                                                break
                                    if not has_assign and not prev_l.startswith((')', ']', '}')) and not prev_l.endswith((':', '{')):
                                        if prev_l.count('(') >= prev_l.count(')') and prev_l.count('[') >= prev_l.count(']'):
                                            output_lines[idx] = output_lines[idx][:indent_len] + "return " + prev_l
                            break
                        idx -= 1
                indent_level = len(block_stack)
                output_lines.append(indent_step * indent_level + f"# end ({popped})")
            else:
                output_lines.append("# end (module/top)")
            continue

        # Check for file_loaded / UI menu block
        if 'file_loaded' in stripped:
            in_menu_block = True
            indent_level = len(block_stack)
            output_lines.append(indent_step * indent_level + f"# {stripped}")
            continue

        if in_menu_block:
            if stripped == 'end':
                in_menu_block = False
                output_lines.append(indent_step * len(block_stack) + "# end (menu block)")
            else:
                output_lines.append(indent_step * len(block_stack) + f"# {stripped}")
            continue

        if in_rescue:
            output_lines.append(indent_step * len(block_stack) + f"# {stripped}")
            continue

        # Check for class definition
        class_match = re.match(r'^class\s+([A-Za-z0-9_.]+)(?:\s*<\s*([A-Za-z0-9_.]+))?', stripped)
        if class_match:
            c_raw = class_match.group(1).replace('::', '.').split('.')[-1]
            inherits = f"({class_match.group(2)})" if class_match.group(2) else ""
            indent_level = len(block_stack)
            output_lines.append(indent_step * indent_level + f"class _Cls_{c_raw}{inherits}:")
            block_stack.append('class')
            continue

        # Check for module definition
        mod_match = re.match(r'^module\s+([A-Za-z0-9_]+)', stripped)
        if mod_match:
            mod_name = mod_match.group(1)
            indent_level = len(block_stack)
            output_lines.append(indent_step * indent_level + f"class _Mod_{mod_name}(RubyModule): pass")
            output_lines.append(indent_step * indent_level + f"{mod_name} = _Mod_{mod_name}('{mod_name}', globals())")
            continue

        # Handle begin
        if stripped == 'begin':
            indent_level = len(block_stack)
            has_begin = True
            output_lines.append(indent_step * indent_level + "# begin")
            continue

        # Handle 'else' and 'elsif'
        if stripped.startswith('else'):
            cur_indent = max(0, len(block_stack) - 1)
            comment = stripped[4:].strip()
            if comment.startswith('#'):
                output_lines.append(indent_step * cur_indent + f"else:  {comment}")
            else:
                output_lines.append(indent_step * cur_indent + "else:")
            continue

        if stripped.startswith(('elsif ', 'elif ')):
            cur_indent = max(0, len(block_stack) - 1)
            p_len = 6 if stripped.startswith('elsif ') else 5
            cond = stripped[p_len:].rstrip(':')
            cond = clean_ruby_lexical(cond)
            if '#' in cond:
                c_part, comment = cond.split('#', 1)
                output_lines.append(indent_step * cur_indent + f"elif {c_part.strip()}:  # {comment.strip()}")
            else:
                output_lines.append(indent_step * cur_indent + f"elif {cond.strip()}:")
            continue

        # --- Lexical cleaning on the stripped line ---
        l = clean_ruby_lexical(stripped)
        if not l.startswith('def '):
            for fn in zero_arg_funcs:
                l = re.sub(r'\b(' + fn + r')\b(?!\s*[\(\[])', r'\1()', l)
        indent_level = len(block_stack)

        # Handle inline .each with trailing if / unless
        m_each_if = re.match(r'^(.*?)\.each\s*\{\s*\|(.*?)\|\s*(.*?)\s*\}\s+if\s+(.*)$', l)
        if m_each_if:
            arr_obj = m_each_if.group(1).replace('.compact', '').strip()
            iter_var = m_each_if.group(2).strip()
            body_stmts = m_each_if.group(3)
            cond = m_each_if.group(4).strip()
            output_lines.append(indent_step * indent_level + f"if {cond}:")
            output_lines.append(indent_step * (indent_level + 1) + f"for {iter_var} in {arr_obj}:")
            for sub_s in body_stmts.split(';'):
                sub_s = sub_s.strip()
                if sub_s:
                    output_lines.append(indent_step * (indent_level + 2) + sub_s)
            continue

        m_each_un = re.match(r'^(.*?)\.each\s*\{\s*\|(.*?)\|\s*(.*?)\s*\}\s+unless\s+(.*)$', l)
        if m_each_un:
            arr_obj = m_each_un.group(1).replace('.compact', '').strip()
            iter_var = m_each_un.group(2).strip()
            body_stmts = m_each_un.group(3)
            cond = m_each_un.group(4).strip()
            output_lines.append(indent_step * indent_level + f"if not ({cond}):")
            output_lines.append(indent_step * (indent_level + 1) + f"for {iter_var} in {arr_obj}:")
            for sub_s in body_stmts.split(';'):
                sub_s = sub_s.strip()
                if sub_s:
                    output_lines.append(indent_step * (indent_level + 2) + sub_s)
            continue

        # Handle line starting with if cond: obj.each { |x| ... }
        m_if_each = re.match(r'^if\s+(.*?):\s*(.*?)\.each\s*\{\s*\|(.*?)\|\s*(.*?)\s*\}$', l)
        if m_if_each:
            cond = m_if_each.group(1).strip()
            arr_obj = m_if_each.group(2).replace('.compact', '').strip()
            iter_var = m_if_each.group(3).strip()
            body_stmts = m_if_each.group(4)
            output_lines.append(indent_step * indent_level + f"if {cond}:")
            output_lines.append(indent_step * (indent_level + 1) + f"for {iter_var} in {arr_obj}:")
            for sub_s in body_stmts.split(';'):
                sub_s = sub_s.strip()
                if sub_s:
                    output_lines.append(indent_step * (indent_level + 2) + sub_s)
            continue

        # Handle inline .each { |var| ... }
        inline_each = re.match(r'^(.*?)\.each\s*\{\s*\|(.*?)\|\s*(.*?)\s*\}$', l)
        if inline_each:
            arr_obj = inline_each.group(1).replace('.compact', '')
            iter_var = inline_each.group(2)
            body_stmts = inline_each.group(3)
            output_lines.append(indent_step * indent_level + f"for {iter_var} in {arr_obj}:")
            for sub_s in body_stmts.split(';'):
                sub_s = sub_s.strip()
                if not sub_s:
                    continue
                # Handle nested inline .each
                sub_each = re.match(r'^(.*?)\.each\s*\{\s*\|(.*?)\|\s*(.*?)\s*\}$', sub_s)
                if sub_each:
                    output_lines.append(indent_step * (indent_level + 1) + f"for {sub_each.group(2).strip()} in {sub_each.group(1).strip()}:")
                    for s3 in sub_each.group(3).split(';'):
                        if s3.strip():
                            output_lines.append(indent_step * (indent_level + 2) + s3.strip())
                    continue
                tif = check_trailing_if(sub_s)
                if tif:
                    sub_s = f"if {tif[1]}: {tif[0]}"
                output_lines.append(indent_step * (indent_level + 1) + sub_s)
            continue

        # Trailing if / unless
        tif = check_trailing_if(l)
        if tif:
            output_lines.append(indent_step * indent_level + f"if {tif[1]}: {tif[0]}")
            continue

        tun = check_trailing_unless(l)
        if tun:
            output_lines.append(indent_step * indent_level + f"if not ({tun[1]}): {tun[0]}")
            continue

        # Lambda / proc definition: name = lambda do |args| ... end
        lambda_do = re.match(r'^(\w+)\s*=\s*(?:lambda|proc)\s+do\s*\|(.*?)\|\s*$', l)
        if lambda_do:
            fn_name = lambda_do.group(1)
            args = lambda_do.group(2)
            l = f"def {fn_name}({args}, *extra_args):"
            output_lines.append(indent_step * indent_level + l)
            block_stack.append('def')
            continue

        # Translate def methods
        def_match = re.match(r'^def\s+([A-Za-z0-9_!?.]+)(?:\s*\((.*)\)|\s+(.*))?\s*$', l)
        if def_match:
            raw_fn = def_match.group(1).replace('!', '_bang').replace('?', '_p')
            fn_name = raw_fn.split('.')[-1]
            inner_args = (def_match.group(2) or def_match.group(3) or "").strip()
            # Convert Ruby keyword args (e.g., name:, axis:, sill: 0.0) to Python
            inner_args = re.sub(r'(\b[a-zA-Z_][a-zA-Z0-9_]*):\s*([^,]+)', r'\1=\2', inner_args)
            inner_args = re.sub(r'(\b[a-zA-Z_][a-zA-Z0-9_]*):', r'\1=None', inner_args)
            if inner_args and '*' not in inner_args:
                clean_args = f"({inner_args}, *extra_args)"
            else:
                clean_args = f"({inner_args})"

            l = f"def {fn_name}{clean_args}:"
            output_lines.append(indent_step * indent_level + l)
            block_stack.append('def')
            continue

        # In function calls, convert Ruby keyword arguments 'name: val' -> 'name=val'
        if '(' in l and ')' in l and ':' in l and not l.startswith('if ') and not l.startswith('while ') and not l.startswith('elif '):
            l = re.sub(r'\blambda\s+(\w+):', r'__LAMBDA__\1__COLON__', l)
            l = re.sub(r'(\b[a-zA-Z_][a-zA-Z0-9_]*):\s*', r'\1=', l)
            l = re.sub(r'__LAMBDA__(\w+)__COLON__', r'lambda \1:', l)

        # Loop: step: start.step(limit, step) do |i|
        step_match = re.match(r'^(.*?)\.step\((.*?),\s*(.*?)\)\s+do\s*\|(.*?)\|\s*$', l)
        if step_match:
            s_val = step_match.group(1).strip()
            l_val = step_match.group(2).strip()
            st_val = step_match.group(3).strip()
            var = step_match.group(4).strip()
            l = f"for {var} in [x * ({st_val}) + ({s_val}) for x in range(int((({l_val}) - ({s_val})) / ({st_val})) + 1)]:"
            output_lines.append(indent_step * indent_level + l)
            block_stack.append('loop')
            continue

        # Loop 1: upto: 0.upto(segments) do |i|
        upto_match = re.match(r'^(.*?)\.upto\((.*?)\)\s+do\s*\|(.*?)\|\s*$', l)
        if upto_match:
            start_val = upto_match.group(1)
            end_val = upto_match.group(2)
            var = upto_match.group(3)
            l = f"for {var} in range({start_val}, ({end_val}) + 1):"
            output_lines.append(indent_step * indent_level + l)
            block_stack.append('loop')
            continue

        # Loop 2: each_cons(2): pts.each_cons(2) do |p1, p2|
        cons_match = re.match(r'^(.*?)\.each_cons\(2\)\s+do\s*\|(.*?)\|\s*$', l)
        if cons_match:
            arr_obj = cons_match.group(1)
            params = cons_match.group(2)
            l = f"for {params} in zip({arr_obj}[:-1], {arr_obj}[1:]):"
            output_lines.append(indent_step * indent_level + l)
            block_stack.append('loop')
            continue

        # Loop 3: times: N.times do |i|
        times_match = re.match(r'^(\d+|\w+)\.times\s+do\s*\|(.*?)\|\s*$', l)
        if times_match:
            cnt = times_match.group(1)
            var = times_match.group(2)
            l = f"for {var} in range({cnt}):"
            output_lines.append(indent_step * indent_level + l)
            block_stack.append('loop')
            continue

        # Loop 4: range each: (0...N).each do |k| or (-5..5).each do |i|
        range_match = re.match(r'^\(?\s*(-?\d+|[A-Za-z0-9_.]+)\s*\.\.\.\s*(-?\d+|[A-Za-z0-9_.]+)\s*\)?\.each\s+do\s*\|(.*?)\|\s*$', l)
        if range_match:
            s = range_match.group(1)
            e = range_match.group(2)
            var = range_match.group(3)
            l = f"for {var} in range({s}, {e}):"
            output_lines.append(indent_step * indent_level + l)
            block_stack.append('loop')
            continue

        range_inc_match = re.match(r'^\(?\s*(-?\d+|[A-Za-z0-9_.]+)\s*\.\.\s*(-?\d+|[A-Za-z0-9_.]+)\s*\)?\.each\s+do\s*\|(.*?)\|\s*$', l)
        if range_inc_match:
            s = range_inc_match.group(1)
            e = range_inc_match.group(2)
            var = range_inc_match.group(3)
            l = f"for {var} in range({s}, ({e}) + 1):"
            output_lines.append(indent_step * indent_level + l)
            block_stack.append('loop')
            continue

        # Loop 5: each_with_index: arr.each_with_index do |item, i|
        ewi_match = re.match(r'^(.*?)\.each_with_index\s+do\s*\|(.*?)\s*,\s*(\w+)\|\s*$', l)
        if ewi_match:
            arr = ewi_match.group(1)
            item = ewi_match.group(2).strip()
            idx = ewi_match.group(3).strip()
            l = f"for {idx}, {item} in enumerate({arr}):"
            output_lines.append(indent_step * indent_level + l)
            block_stack.append('loop')
            continue

        # Loop 6: each: arr.each do |item|
        each_match = re.match(r'^(.*?)\.each\s+do\s*\|(.*?)\|\s*$', l)
        if each_match:
            arr = each_match.group(1).strip()
            item = each_match.group(2).strip()
            m_rng = re.match(r'^\(?\s*(-?\d+|[A-Za-z0-9_.]+)\s*(\.\.\.?)\s*(-?\d+|[A-Za-z0-9_.]+)\s*\)?$', arr)
            if m_rng:
                r_start, r_dots, r_end = m_rng.group(1), m_rng.group(2), m_rng.group(3)
                if r_dots == '...':
                    arr = f"range({r_start}, {r_end})"
                else:
                    arr = f"range({r_start}, ({r_end}) + 1)"
            elif arr.startswith('{') and arr.endswith('}') and ',' in item:
                arr = f"{arr}.items()"
            else:
                arr = f"_ruby_iter({arr})"
            l = f"for {item} in {arr}:"
            output_lines.append(indent_step * indent_level + l)
            block_stack.append('loop')
            continue

        # Loop 8: Map loop: result = arr.map do |item| (MUST be before generic do)
        map_do = re.match(r'^(\w+)\s*=\s*(.*?)\.map\s+do\s*\|(.*?)\|\s*$', l)
        if map_do:
            target = map_do.group(1).strip()
            arr = map_do.group(2).strip()
            var = map_do.group(3).strip()
            output_lines.append(indent_step * indent_level + f"{target} = []")
            output_lines.append(indent_step * indent_level + f"for {var} in {arr}:")
            block_stack.append(f'map:{target}')
            continue

        # Loop 7: Generic caller do |args| (e.g. CSV.open(...) do |csv|)
        generic_do = re.match(r'^(.*?)\s+do\s*\|(.*?)\|\s*$', l)
        if generic_do:
            caller = generic_do.group(1).strip()
            var = generic_do.group(2).strip()
            if 'open(' in caller or 'File.' in caller or 'CSV.' in caller:
                l = f"with {caller} as {var}:"
                output_lines.append(indent_step * indent_level + l)
                block_stack.append('with')
                continue
            else:
                l = f"for {var} in {caller}:"
                output_lines.append(indent_step * indent_level + l)
                block_stack.append('loop')
                continue

        # Translate for cond (including Ruby ranges like -5..5, 0...10, etc.)
        for_match = re.match(r'^for\s+(.*)$', l)
        if for_match:
            cond = for_match.group(1).rstrip(':')
            comment_str = ""
            if '#' in cond:
                c_part, comment = cond.split('#', 1)
                cond = c_part.strip()
                comment_str = f"  # {comment.strip()}"
            m_in = re.match(r'^([A-Za-z0-9_,\s]+)\s+in\s+(.*)$', cond.strip())
            if m_in:
                vname = m_in.group(1).strip()
                iter_expr = m_in.group(2).strip()
                m_rng = re.match(r'^\(?\s*(-?\d+|[A-Za-z0-9_.]+)\s*(\.\.\.?)\s*(-?\d+|[A-Za-z0-9_.]+)\s*\)?$', iter_expr)
                if m_rng:
                    r_start = m_rng.group(1)
                    r_dots = m_rng.group(2)
                    r_end = m_rng.group(3)
                    if r_dots == '...':
                        iter_expr = f"range({r_start}, {r_end})"
                    else:
                        iter_expr = f"range({r_start}, ({r_end}) + 1)"
                l = f"for {vname} in {iter_expr}:{comment_str}"
            else:
                l = f"for {cond.strip()}:{comment_str}"
            output_lines.append(indent_step * indent_level + l)
            block_stack.append('loop')
            continue

        # Translate while cond
        while_match = re.match(r'^while\s+(.*)$', l)
        if while_match:
            cond = while_match.group(1).rstrip(':')
            if '#' in cond:
                c_part, comment = cond.split('#', 1)
                l = f"while {c_part.strip()}:  # {comment.strip()}"
            else:
                l = f"while {cond.strip()}:"
            output_lines.append(indent_step * indent_level + l)
            block_stack.append('while')
            continue

        # Single-line if (already converted, e.g. from trailing if/unless)
        if re.match(r'^if\s+.*?:.+', l):
            output_lines.append(indent_step * indent_level + l)
            continue

        # Translate if cond
        if_match = re.match(r'^if\s+(.*)$', l)
        if if_match:
            cond = if_match.group(1).rstrip(':')
            if '#' in cond:
                c_part, comment = cond.split('#', 1)
                l = f"if {c_part.strip()}:  # {comment.strip()}"
            else:
                l = f"if {cond.strip()}:"
            output_lines.append(indent_step * indent_level + l)
            block_stack.append('if')
            continue

        # Translate unless cond
        unless_match = re.match(r'^unless\s+(.*)$', l)
        if unless_match:
            cond = unless_match.group(1).rstrip(':')
            if '#' in cond:
                c_part, comment = cond.split('#', 1)
                l = f"if not ({c_part.strip()}):  # {comment.strip()}"
            else:
                l = f"if not ({cond.strip()}):"
            output_lines.append(indent_step * indent_level + l)
            block_stack.append('if')
            continue

        output_lines.append(indent_step * indent_level + l)

    return "\n".join(output_lines)


# ==============================================================================
# 3. EXECUTION & EXPORT TO WAVEFRONT OBJ
# ==============================================================================

def execute_ruby_script(rb_code):
    """
    Thực thi mã SketchUp Ruby trong môi trường Python Mock và thu thập dữ liệu hình học.
    """
    model = SketchupMock.reset()

    sandbox_globals = {
        'Sketchup': SketchupMock,
        'Geom': GeomMock,
        'UI': UIMock,
        'Point3d': Point3d,
        'Vector3d': Vector3d,
        'Color': Color,
        'Material': Material,
        'Face': Face,
        'Group': Group,
        'RubyList': RubyList,
        'RubyModule': RubyModule,
        '_RubyState': _RubyState,
        '_RB_STATE': _RubyState(),
        'X_AXIS': X_AXIS,
        'Y_AXIS': Y_AXIS,
        'Z_AXIS': Z_AXIS,
        'ORIGIN': ORIGIN,
        'Z_UP': Z_AXIS,
        'CSV': CSVMock,
        'CSVMock': CSVMock,
        'File': FileMock,
        'FileMock': FileMock,
        'ENV': os.environ,
        'Edge': Edge,
        'Vertex': Vertex,
        'Loop': Loop,
        'SketchupModel': SketchupModel,
        'TextAlignCenter': 1,
        'TextAlignLeft': 0,
        'TextAlignRight': 2,
        'face_box': face_box,
        'box': box,
        'add_box': add_box,
        'group_box': group_box,
        'add_round_bar': add_round_bar,
        'cyl': cyl,
        'cylinder': cylinder,
        'math': math,
        'Math': math,
        'puts': print,
        'model': model,
        'entities': model.entities,
        'materials': model.materials,
        'layers': model.layers,
        '_ruby_iter': lambda obj: obj.items() if isinstance(obj, dict) else obj,
    }

    py_code = transpile_ruby_to_python(rb_code)

    try:
        exec(py_code, sandbox_globals)
    except Exception as ex:
        tb = sys.exc_info()[2]
        lineno = "?"
        while tb:
            if tb.tb_frame.f_code.co_filename == "<string>":
                lineno = tb.tb_lineno
            tb = tb.tb_next
        raise RuntimeError(f"Lỗi thực thi mã Ruby tại dòng ~{lineno}: {str(ex)}")

    # 1. Setup materials if defined
    for fn in ['setup_materials', 'create_materials', 'init_materials']:
        if fn in sandbox_globals and callable(sandbox_globals[fn]):
            try:
                import inspect
                sig = inspect.signature(sandbox_globals[fn])
                if len(sig.parameters) == 0:
                    sandbox_globals[fn]()
                else:
                    sandbox_globals[fn](model)
            except Exception as e:
                print(f"[Engine] Notice during {fn}(): {e}")

    # 2. Check if a build/create method was defined and needs explicit execution
    for fn in ['build', 'create_model', 'generate', 'create_sign', 'run', 'create_structure', 'build_model']:
        if fn in sandbox_globals and callable(sandbox_globals[fn]):
            try:
                import inspect
                sig = inspect.signature(sandbox_globals[fn])
                if len(sig.parameters) == 0:
                    sandbox_globals[fn]()
                elif len(sig.parameters) == 1:
                    sandbox_globals[fn](model)
                else:
                    sandbox_globals[fn](model.entities)
            except Exception as e:
                print(f"[Engine] Notice during {fn}(): {e}")

    # 3. If model is still empty, scan modules for build methods
    faces_check = collect_all_faces(model.entities)
    if not faces_check:
        for k, v in list(sandbox_globals.items()):
            if isinstance(v, RubyModule):
                for m_fn in ['create_model', 'build', 'run', 'create']:
                    func = v._scope.get(m_fn)
                    if func and callable(func):
                        try:
                            func()
                        except Exception:
                            try:
                                func(model)
                            except Exception:
                                pass

    return model


def collect_all_faces(entities, current_group_name="Default"):
    faces_data = []

    for f in entities.faces:
        if len(f.pts) >= 3:
            faces_data.append({
                "face": f,
                "group": current_group_name,
                "material": getattr(f.material, 'name', None) or 'mat_default'
            })

    for g in entities.groups:
        sub_name = g.name or current_group_name
        faces_data.extend(collect_all_faces(g.entities, current_group_name=sub_name))

    return faces_data


def export_model_to_obj(model, output_dir, base_name="ruby_model"):
    """
    Xuất Model đã dựng sang file .obj và .mtl.
    """
    os.makedirs(output_dir, exist_ok=True)
    obj_path = os.path.join(output_dir, f"{base_name}.obj")
    mtl_path = os.path.join(output_dir, f"{base_name}.mtl")
    mtl_filename = f"{base_name}.mtl"

    all_faces_meta = collect_all_faces(model.entities)
    if not all_faces_meta:
        raise ValueError("Mô hình không chứa bề mặt hình học (faces) nào để xuất 3D OBJ!")

    materials_used = set()
    for item in all_faces_meta:
        materials_used.add(item["material"])

    # Write MTL file
    with open(mtl_path, "w", encoding="utf-8") as fmtl:
        fmtl.write(f"# Materials for {base_name}\n\n")
        fmtl.write("newmtl mat_default\nKd 0.82 0.82 0.85\nKa 0.2 0.2 0.2\nKs 0.1 0.1 0.1\nNs 10.0\nd 1.0\n\n")

        for m_name in materials_used:
            if m_name == 'mat_default':
                continue
            mat_obj = model.materials.get(m_name)
            if mat_obj and hasattr(mat_obj, 'color'):
                if isinstance(mat_obj.color, (list, tuple)):
                    rgb = Color(*mat_obj.color).to_rgb_norm()
                elif hasattr(mat_obj.color, 'to_rgb_norm'):
                    rgb = mat_obj.color.to_rgb_norm()
                else:
                    rgb = (0.75, 0.75, 0.75)
                alpha = mat_obj.alpha if hasattr(mat_obj, 'alpha') else 1.0
            else:
                rgb = (0.75, 0.75, 0.75)
                alpha = 1.0

            fmtl.write(f"newmtl {m_name}\n")
            fmtl.write(f"Kd {rgb[0]:.3f} {rgb[1]:.3f} {rgb[2]:.3f}\n")
            fmtl.write("Ka 0.25 0.25 0.25\n")
            fmtl.write("Ks 0.15 0.15 0.15\n")
            fmtl.write("Ns 20.0\n")
            fmtl.write(f"d {alpha:.2f}\n\n")

    # Write OBJ file
    vertices = []
    vertex_map = {}

    def get_vertex_idx(pt):
        key = (round(pt.x, 4), round(pt.y, 4), round(pt.z, 4))
        if key not in vertex_map:
            vertices.append(key)
            vertex_map[key] = len(vertices)
        return vertex_map[key]

    face_lines = []
    current_group = None
    current_mat = None

    for item in all_faces_meta:
        f = item["face"]
        grp = item["group"]
        mat = item["material"]

        if grp != current_group:
            current_group = grp
            face_lines.append(f"\no {current_group}\n")
        if mat != current_mat:
            current_mat = mat
            face_lines.append(f"usemtl {current_mat}\n")

        idx_list = [get_vertex_idx(p) for p in f.pts]
        if len(idx_list) == 3:
            face_lines.append(f"f {idx_list[0]} {idx_list[1]} {idx_list[2]}\n")
        elif len(idx_list) == 4:
            face_lines.append(f"f {idx_list[0]} {idx_list[1]} {idx_list[2]} {idx_list[3]}\n")
        elif len(idx_list) > 4:
            p0 = idx_list[0]
            for i in range(1, len(idx_list) - 1):
                face_lines.append(f"f {p0} {idx_list[i]} {idx_list[i+1]}\n")

    with open(obj_path, "w", encoding="utf-8") as fobj:
        fobj.write(f"# Wavefront OBJ File\n")
        fobj.write(f"# Object Name: {base_name}\n")
        fobj.write(f"mtllib {mtl_filename}\n\n")
        for v in vertices:
            fobj.write(f"v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n")
        fobj.write("".join(face_lines))

    import trimesh
    tm = trimesh.load(obj_path, force="mesh")
    bmin = tm.bounds[0]
    bmax = tm.bounds[1]

    stats = {
        "obj_filename": f"{base_name}.obj",
        "mtl_filename": mtl_filename,
        "obj_path": obj_path,
        "mtl_path": mtl_path,
        "obj_url": f"/api/rb/3d-models/{base_name}.obj",
        "mtl_url": f"/api/rb/3d-models/{base_name}.mtl",
        "vertices": int(len(tm.vertices)),
        "faces": int(len(tm.faces)),
        "width_m": round(float(bmax[0] - bmin[0]), 2),
        "depth_m": round(float(bmax[1] - bmin[1]), 2),
        "height_m": round(float(bmax[2] - bmin[2]), 2),
        "file_size_kb": round(os.path.getsize(obj_path) / 1024, 1),
        "materials_count": len(materials_used),
        "materials": list(materials_used)
    }

    return stats


def convert_rb_code_to_obj(rb_code=None, base_name="ruby_model", code=None, file_name=None):
    """Quy trình toàn diện: Chuyển đổi mã Ruby -> 3D OBJ & MTL."""
    actual_code = rb_code if rb_code is not None else (code or "")
    actual_name = file_name if file_name is not None else base_name
    clean_base = re.sub(r'[^\w\-]+', '_', actual_name).strip('_') or "ruby_model"
    model = execute_ruby_script(actual_code)
    stats = export_model_to_obj(model, RUBY_EXPORTS_DIR, base_name=clean_base)
    return stats


def list_sample_rb_files():
    """Lấy danh sách các file .rb có sẵn trong thư mục dự án."""
    samples = []
    for f in Path(CURRENT_DIR).glob("*.rb"):
        samples.append({
            "name": f.name,
            "path": str(f),
            "size_kb": round(f.stat().st_size / 1024, 1)
        })
    return samples
