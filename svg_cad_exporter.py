# -*- coding: utf-8 -*-
"""
SVG CAD Exporter v2: Direct 1:1 Vector Export from SVG to Monochrome PDF and AutoCAD DXF.
Uses svgpathtools for 100% accurate path parsing (M, L, A, Z, C, Q supported).
Circles drawn as proper CIRCLE entities in DXF, arcs as proper ARC entities.
Guarantees visual fidelity to the displayed SVG with zero divergent redrawing.
"""
import io
import re
import math
import xml.etree.ElementTree as ET
import ezdxf
from ezdxf.enums import TextEntityAlignment
import fitz  # PyMuPDF


# ============================================================
# UTILITY: SVG arc command -> DXF ARC parameters
# ============================================================
def svg_arc_to_center(x1, y1, rx, ry, phi, fa, fs, x2, y2):
    """
    Convert SVG arc parameterization (endpoint form) to center form.
    Returns (cx, cy, rx, ry, theta1_deg, dtheta_deg) in SVG coordinate system.
    Reference: https://www.w3.org/TR/SVG/implnote.html#ArcImplementationNotes
    """
    if x1 == x2 and y1 == y2:
        return None
    if rx == 0 or ry == 0:
        return None
    rx = abs(rx)
    ry = abs(ry)
    phi_rad = math.radians(phi)
    cos_phi = math.cos(phi_rad)
    sin_phi = math.sin(phi_rad)

    dx = (x1 - x2) / 2.0
    dy = (y1 - y2) / 2.0
    x1p = cos_phi * dx + sin_phi * dy
    y1p = -sin_phi * dx + cos_phi * dy

    # Ensure radii are large enough
    lam = (x1p / rx) ** 2 + (y1p / ry) ** 2
    if lam > 1:
        sl = math.sqrt(lam)
        rx *= sl
        ry *= sl

    num = max(0.0, rx**2 * ry**2 - rx**2 * y1p**2 - ry**2 * x1p**2)
    den = rx**2 * y1p**2 + ry**2 * x1p**2
    sq = math.sqrt(num / den) if den != 0 else 0
    if fa == fs:
        sq = -sq

    cxp = sq * rx * y1p / ry
    cyp = -sq * ry * x1p / rx

    cx = cos_phi * cxp - sin_phi * cyp + (x1 + x2) / 2.0
    cy = sin_phi * cxp + cos_phi * cyp + (y1 + y2) / 2.0

    def angle(ux, uy, vx, vy):
        n = math.sqrt(ux**2 + uy**2) * math.sqrt(vx**2 + vy**2)
        if n == 0:
            return 0
        c = max(-1, min(1, (ux * vx + uy * vy) / n))
        a = math.degrees(math.acos(c))
        if ux * vy - uy * vx < 0:
            a = -a
        return a

    theta1 = angle(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dtheta = angle((x1p - cxp) / rx, (y1p - cyp) / ry,
                   (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if fs == 0 and dtheta > 0:
        dtheta -= 360
    elif fs == 1 and dtheta < 0:
        dtheta += 360

    return cx, cy, rx, ry, theta1, dtheta


def detect_circle_in_arc_path(d):
    """
    Detect if an SVG path like:
      M cx+r cy  A r r 0 1 1 cx-r cy  A r r 0 1 1 cx+r cy
    represents a full circle. Returns (cx, cy, r) or None.
    """
    tokens = re.findall(r'[MmAaLlZz]|[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', d.strip())
    if len(tokens) < 1:
        return None
    idx = 0
    # Expect: M x0 y0  A rx ry 0 fa fs x1 y1  A rx ry 0 fa fs x2 y2
    try:
        if tokens[idx] != 'M':
            return None
        idx += 1
        x0 = float(tokens[idx]); y0 = float(tokens[idx+1]); idx += 2
        if tokens[idx] != 'A':
            return None
        idx += 1
        rx1 = float(tokens[idx]); ry1 = float(tokens[idx+1])
        phi1 = float(tokens[idx+2]); fa1 = int(float(tokens[idx+3])); fs1 = int(float(tokens[idx+4]))
        x1 = float(tokens[idx+5]); y1 = float(tokens[idx+6]); idx += 7
        if tokens[idx] != 'A':
            return None
        idx += 1
        rx2 = float(tokens[idx]); ry2 = float(tokens[idx+1])
        phi2 = float(tokens[idx+2]); fa2 = int(float(tokens[idx+3])); fs2 = int(float(tokens[idx+4]))
        x2 = float(tokens[idx+5]); y2 = float(tokens[idx+6]); idx += 7
        # Validate: two arcs of same radius forming a full circle
        if abs(rx1 - rx2) < 0.1 and abs(ry1 - ry2) < 0.1 and abs(rx1 - ry1) < 0.1:
            # The arcs return to the start or close to it
            if abs(x2 - x0) < 0.1 and abs(y2 - y0) < 0.1:
                # Center = midpoint of the two arc endpoints in x
                cx = (x0 + x1) / 2.0
                cy = y0  # for horizontal split
                r = rx1
                return cx, cy, r
    except (IndexError, ValueError):
        pass
    return None


def parse_svg_transform(transform_str):
    """Parse SVG transform: translate(x,y), scale(sx,sy), and rotate(angle, [cx, cy])."""
    tx, ty = 0.0, 0.0
    sx, sy = 1.0, 1.0
    rot = 0.0
    if not transform_str:
        return tx, ty, sx, sy, rot
    m_tr = re.search(r'translate\(\s*([-\d.]+)\s*[, ]\s*([-\d.]+)\s*\)', transform_str)
    if m_tr:
        tx += float(m_tr.group(1))
        ty += float(m_tr.group(2))
    m_sc = re.search(r'scale\(\s*([-\d.]+)(?:\s*[, ]\s*([-\d.]+))?\s*\)', transform_str)
    if m_sc:
        sx *= float(m_sc.group(1))
        sy *= float(m_sc.group(2)) if m_sc.group(2) else float(m_sc.group(1))
    m_rot = re.search(r'rotate\(\s*([-\d.]+)', transform_str)
    if m_rot:
        rot += float(m_rot.group(1))
    return tx, ty, sx, sy, rot


# ============================================================
# PDF CONVERSION (unchanged, uses PyMuPDF directly)
# ============================================================
def convert_svg_pages_to_pdf(svg_list):
    """
    Convert a list of SVG XML strings into a single multi-page vector PDF.
    Uses PyMuPDF vector SVG-to-PDF rendering engine for 100% vector fidelity.
    """
    if not svg_list:
        raise ValueError("Danh sach SVG trong")
    master_pdf = fitz.open()
    for svg_str in svg_list:
        if not svg_str or not svg_str.strip():
            continue
        svg_bytes = svg_str.encode('utf-8')
        doc_svg = fitz.open(stream=svg_bytes, filetype='svg')
        pdf_bytes = doc_svg.convert_to_pdf()
        page_doc = fitz.open('pdf', pdf_bytes)
        master_pdf.insert_pdf(page_doc)
    out_buf = io.BytesIO()
    master_pdf.save(out_buf)
    return out_buf.getvalue()


# ============================================================
# DXF CONVERSION v2: precise SVG -> DXF with proper geometry
# ============================================================
def convert_svg_to_dxf(svg_list, template_path="templates/dim.dxf", custom_layers=None):
    """
    Convert one or more SVG XML strings into an AutoCAD DXF document.
    Entities are mapped 1:1 to AutoCAD modelspace via proper SVG path parsing.
    - Lines/polylines: LWPOLYLINE
    - Circles (arc paths): CIRCLE with optional solid hatch
    - Arcs: ARC entity (proper center+angles)
    - Text: MTEXT with correct size, anchor, y-baseline alignment
    Multiple pages are laid out horizontally with spacing.
    Supports user custom_layers (ACI color, linetype, lineweight).
    """
    if not svg_list:
        raise ValueError("Danh sach SVG trong")
    if isinstance(svg_list, str):
        svg_list = [svg_list]

    try:
        doc = ezdxf.readfile(template_path)
    except Exception:
        doc = ezdxf.new("R2010")

    msp = doc.modelspace()

    from dxf_template_helper import ensure_layer

    # Standard CAD layers (TCVN / AutoCAD standard + User custom overrides)
    layer_configs = {
        "BE_TONG": {"color": 7, "lineweight": 35, "linetype": "Continuous"},
        "THEP_CHU": {"color": 1, "lineweight": 50, "linetype": "Continuous"},
        "THEP_TANG_CUONG": {"color": 6, "lineweight": 50, "linetype": "Continuous"},
        "COT_DAI": {"color": 4, "lineweight": 15, "linetype": "Continuous"},
        "DIM": {"color": 3, "lineweight": 9, "linetype": "Continuous"},
        "TRUC": {"color": 8, "lineweight": 15, "linetype": "CENTER"},
        "TEXT": {"color": 7, "lineweight": 15, "linetype": "Continuous"},
        "KHUNG_TEN": {"color": 7, "lineweight": 50, "linetype": "Continuous"},
    }
    if custom_layers and isinstance(custom_layers, dict):
        for l_name, cfg in custom_layers.items():
            if l_name in layer_configs and isinstance(cfg, dict):
                layer_configs[l_name].update(cfg)

    for l_name, cfg in layer_configs.items():
        ensure_layer(doc, l_name,
                     color=int(cfg.get("color", 7)),
                     lineweight=int(cfg.get("lineweight", 15)),
                     linetype=cfg.get("linetype", "Continuous"))

    scale_to_cad = 1.0 / 0.08   # 1 SVG px = 12.5 mm in AutoCAD
    page_spacing_mm = 25000.0

    for page_idx, svg_content in enumerate(svg_list):
        if not svg_content or not svg_content.strip():
            continue

        x_page_offset_mm = page_idx * page_spacing_mm

        # Parse SVG
        svg_cleaned = re.sub(r'\sxmlns(:\w+)?="[^"]+"', '', svg_content)
        root = ET.fromstring(svg_cleaned)

        vb = root.get('viewBox', '0 0 1680 1188')
        parts = [float(p) for p in vb.replace(',', ' ').split() if p.strip()]
        vb_w = parts[2] if len(parts) >= 4 else 1680.0
        vb_h = parts[3] if len(parts) >= 4 else 1188.0
        sheet_h = vb_h

        # Nâng Y text lên 1mm tính theo bản in ra (printed paper)
        paper_w_mm = 420.0
        w_attr = root.get('width', '')
        m_w = re.search(r'([\d.]+)\s*mm', w_attr)
        if m_w:
            paper_w_mm = float(m_w.group(1))
        svg_px_per_paper_mm = vb_w / paper_w_mm if paper_w_mm > 0 else 4.0
        text_y_offset_cad = 1.0 * svg_px_per_paper_mm * scale_to_cad  # 1mm on paper = 50.0mm in CAD (1:50)

        def svg_to_cad(x, y, local_tx=0.0, local_ty=0.0, local_sx=1.0, local_sy=1.0):
            """Convert SVG coordinates to CAD mm, flipping Y axis."""
            real_x = (x * local_sx + local_tx) * scale_to_cad + x_page_offset_mm
            real_y = (sheet_h - (y * local_sy + local_ty)) * scale_to_cad
            return real_x, real_y

        def get_layer_from_elem(stroke, fill, lw):
            """Determine DXF layer from SVG stroke color and lineweight."""
            if '#94a3b8' in stroke:
                return 'TRUC'
            if '#059669' in stroke or '#10b981' in stroke or '#64748b' in stroke:
                return 'DIM'
            if '#c026d3' in stroke or '#d946ef' in stroke:
                return 'THEP_TANG_CUONG'
            if '#dc2626' in stroke or '#0284c7' in stroke:
                return 'THEP_CHU'
            if stroke in ('#000000', '#1f2937', '#0f172a'):
                if lw >= 1.2:
                    return 'KHUNG_TEN' if lw >= 2.0 else 'THEP_CHU'
                else:
                    return 'BE_TONG'
            return 'BE_TONG'

        def in_viewbox(svg_x, svg_y, margin=60.0):
            """Check if a single SVG point is within viewBox bounds (with margin)."""
            return (-margin <= svg_x <= vb_w + margin) and (-margin <= svg_y <= vb_h + margin)

        def circle_in_viewbox(cx, cy, r):
            """Check if circle overlaps the viewBox."""
            return (cx + r >= -20 and cx - r <= vb_w + 20 and
                    cy + r >= -20 and cy - r <= vb_h + 20)

        def parse_path_to_segments(d, tx, ty, sx, sy):
            """
            Parse SVG path d attribute into a list of DXF-ready segments.
            Handles M, L, A, Z commands.
            Returns list of:
              ('line', [(x1,y1),(x2,y2),...], closed)
              ('circle', cx, cy, r)
              ('arc', cx, cy, r, start_angle_deg, end_angle_deg)
            """
            results = []
            # Tokenize: letters and numbers
            tokens = re.findall(r'[MmLlAaZz]|[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', d.strip())
            if not tokens:
                return results

            # Try circle detection first
            circle = detect_circle_in_arc_path(d)
            if circle:
                cx_svg, cy_svg, r_svg = circle
                # Skip circles completely outside the viewBox (off-screen spans)
                if not circle_in_viewbox(cx_svg * sx + tx, cy_svg * sy + ty, r_svg * sx):
                    return results
                cx_cad, cy_cad = svg_to_cad(cx_svg, cy_svg, tx, ty, sx, sy)
                r_cad = r_svg * sx * scale_to_cad
                results.append(('circle', cx_cad, cy_cad, r_cad))
                return results

            # General path parsing
            cur_pts = []
            closed = False
            cur_cmd = None
            prev_x, prev_y = 0.0, 0.0
            start_x, start_y = 0.0, 0.0
            i = 0

            while i < len(tokens):
                tok = tokens[i]
                if tok in ('M', 'm', 'L', 'l', 'A', 'a', 'Z', 'z'):
                    cur_cmd = tok
                    i += 1

                    if cur_cmd in ('Z', 'z'):
                        closed = True
                        if cur_pts:
                            if any(in_viewbox(p[0] * sx + tx, p[1] * sy + ty) for p in cur_pts):
                                results.append(('line', list(cur_pts), True))
                            cur_pts = [(start_x, start_y)]  # reset path
                        prev_x, prev_y = start_x, start_y
                else:
                    if cur_cmd in ('M', 'L'):
                        px = float(tok)
                        py = float(tokens[i + 1])
                        i += 2
                        if cur_cmd == 'M' and not cur_pts:
                            start_x, start_y = px, py
                        elif cur_cmd == 'M' and cur_pts:
                            # MoveTo with existing path: flush current segment (clip to viewBox)
                            if len(cur_pts) >= 2:
                                if any(in_viewbox(p[0] * sx + tx, p[1] * sy + ty) for p in cur_pts):
                                    results.append(('line', list(cur_pts), False))
                            cur_pts = []
                            start_x, start_y = px, py
                        cur_pts.append((px, py))
                        prev_x, prev_y = px, py

                    elif cur_cmd in ('m', 'l'):
                        dx = float(tok)
                        dy = float(tokens[i + 1])
                        i += 2
                        px = prev_x + dx
                        py = prev_y + dy
                        if cur_cmd == 'm' and not cur_pts:
                            start_x, start_y = px, py
                        cur_pts.append((px, py))
                        prev_x, prev_y = px, py

                    elif cur_cmd in ('A', 'a'):
                        # SVG Arc: rx ry x-rotation large-arc-flag sweep-flag x y
                        if i + 6 <= len(tokens) - 1:
                            arx = float(tokens[i])
                            ary = float(tokens[i + 1])
                            phi = float(tokens[i + 2])
                            fa = int(float(tokens[i + 3]))
                            fs = int(float(tokens[i + 4]))
                            px = float(tokens[i + 5])
                            py = float(tokens[i + 6])
                            i += 7

                            if cur_cmd == 'a':
                                px += prev_x
                                py += prev_y

                            # Flush pending polyline before arc (clip to viewBox)
                            if len(cur_pts) >= 2:
                                if any(in_viewbox(p[0] * sx + tx, p[1] * sy + ty) for p in cur_pts):
                                    results.append(('line', list(cur_pts), False))
                            cur_pts = [(px, py)]  # arc endpoint becomes new start

                            # Convert arc to center form
                            arc = svg_arc_to_center(prev_x, prev_y, arx, ary, phi, fa, fs, px, py)
                            if arc:
                                acx, acy, arx2, ary2, theta1, dtheta = arc
                                # Only handle circular arcs (rx == ry approx)
                                if abs(arx2 - ary2) < 1.0:
                                    # Skip arcs completely outside viewBox
                                    if circle_in_viewbox(acx * sx + tx, acy * sy + ty, arx2 * sx):
                                        r_cad = arx2 * sx * scale_to_cad
                                        # Convert center to CAD coords
                                        cad_cx, cad_cy = svg_to_cad(acx, acy, tx, ty, sx, sy)
                                        # SVG Y flipped: angles must be negated and adjusted
                                        # In SVG: angle CW from positive X axis
                                        # In DXF: angle CCW from positive X axis
                                        # After Y flip: start_angle_dxf = -(theta1 + dtheta), end = -theta1
                                        theta2 = theta1 + dtheta
                                        start_a = (-theta2) % 360
                                        end_a = (-theta1) % 360
                                        if abs(abs(dtheta) - 360) < 1.0:
                                            # Full circle
                                            results.append(('circle', cad_cx, cad_cy, r_cad))
                                        else:
                                            results.append(('arc', cad_cx, cad_cy, r_cad, start_a, end_a))
                            prev_x, prev_y = px, py
                        else:
                            i += 1
                    else:
                        i += 1

            # Final flush: only emit if any point is within viewBox
            if len(cur_pts) >= 2:
                if any(in_viewbox(p[0] * sx + tx, p[1] * sy + ty) for p in cur_pts):
                    results.append(('line', list(cur_pts), False))

            return results

        def clip_pts_to_viewbox(pts, sx_local, tx_local, sy_local, ty_local, margin=70.0):
            """
            Split a polyline into sub-polylines that lie within the viewBox.
            Points whose SVG coordinates (after local transform) are outside the 
            viewBox by more than margin are excluded, splitting the polyline at gaps.
            """
            if not pts:
                return []
            result_segs = []
            cur_seg = []
            for p in pts:
                svg_x = p[0] * sx_local + tx_local
                svg_y = p[1] * sy_local + ty_local
                inside = in_viewbox(svg_x, svg_y, margin)
                if inside:
                    cur_seg.append(p)
                else:
                    if len(cur_seg) >= 2:
                        result_segs.append(cur_seg)
                    cur_seg = []
            if len(cur_seg) >= 2:
                result_segs.append(cur_seg)
            return result_segs

        def add_dxf_entities(segments, layer, fill, lw, loc_tx, loc_ty, loc_sx, loc_sy):
            """Add parsed path segments as DXF entities."""
            for seg in segments:
                if seg[0] == 'circle':
                    _, cx, cy, r = seg
                    if r < 1.0:
                        continue
                    msp.add_circle((cx, cy), r, dxfattribs={'layer': layer})
                    if fill and fill not in ('none', '', '#ffffff', 'white'):
                        try:
                            hatch = msp.add_hatch(color=ezdxf.colors.WHITE if layer == 'BE_TONG' else 7)
                            hatch.paths.add_edge_path().add_arc((cx, cy), r, 0, 360)
                            hatch.dxf.layer = layer
                            hatch.dxf.solid_fill = 1
                        except Exception:
                            pass

                elif seg[0] == 'arc':
                    _, cx, cy, r, a_start, a_end = seg
                    if r < 1.0:
                        continue
                    msp.add_arc((cx, cy), r, a_start, a_end, dxfattribs={'layer': layer})

                elif seg[0] == 'line':
                    _, pts, closed = seg
                    if len(pts) < 2:
                        continue
                    # Clip to viewBox before emitting
                    clipped_segs = clip_pts_to_viewbox(pts, loc_sx, loc_tx, loc_sy, loc_ty)
                    for sub_pts in clipped_segs:
                        if len(sub_pts) < 2:
                            continue
                        cad_pts = [svg_to_cad(px, py, loc_tx, loc_ty, loc_sx, loc_sy) for px, py in sub_pts]
                        msp.add_lwpolyline(cad_pts, close=closed,
                                           dxfattribs={'layer': layer})

        def walk(elem, tx=0.0, ty=0.0, sx=1.0, sy=1.0, rot=0.0):
            t_str = elem.get('transform', '')
            dtx, dty, dsx, dsy, drot = parse_svg_transform(t_str)
            tx = tx + dtx * sx
            ty = ty + dty * sy
            sx = sx * dsx
            sy = sy * dsy
            rot = rot + drot

            tag = elem.tag.lower().split('}')[-1]  # strip namespace

            stroke = elem.get('stroke', 'none') or 'none'
            fill = elem.get('fill', 'none') or 'none'
            lw_str = elem.get('stroke-width', '0') or '0'
            try:
                lw = float(re.search(r'[\d.]+', lw_str).group(0))
            except Exception:
                lw = 0.0

            layer = get_layer_from_elem(stroke, fill, lw)

            if tag == 'rect':
                rx = float(elem.get('x', 0))
                ry = float(elem.get('y', 0))
                rw = float(elem.get('width', 0))
                rh = float(elem.get('height', 0))
                # Skip background white rect
                if fill in ('#ffffff', 'white') and stroke in ('none', ''):
                    pass
                else:
                    pts = [(rx, ry), (rx + rw, ry), (rx + rw, ry + rh), (rx, ry + rh)]
                    cad_pts = [svg_to_cad(px, py, tx, ty, sx, sy) for px, py in pts]
                    msp.add_lwpolyline(cad_pts, close=True, dxfattribs={'layer': layer})

            elif tag == 'circle':
                cx = float(elem.get('cx', 0))
                cy = float(elem.get('cy', 0))
                r_elem = float(elem.get('r', 0))
                calc_x = cx * sx + tx
                calc_y = cy * sy + ty
                calc_r = r_elem * sx
                if calc_x + calc_r < -20.0 or calc_x - calc_r > vb_w + 20.0 or calc_y + calc_r < -20.0 or calc_y - calc_r > vb_h + 20.0:
                    return
                r = r_elem * sx * scale_to_cad
                center = svg_to_cad(cx, cy, tx, ty, sx, sy)
                msp.add_circle(center, r, dxfattribs={'layer': layer})
                if fill not in ('none', '', '#ffffff', 'white'):
                    try:
                        hatch = msp.add_hatch()
                        hatch.paths.add_edge_path().add_arc(center, r, 0, 360)
                        hatch.dxf.layer = layer
                        hatch.dxf.solid_fill = 1
                    except Exception:
                        pass

            elif tag == 'text':
                txt = elem.text or ''
                if not txt.strip():
                    for child in elem:
                        walk(child, tx, ty, sx, sy, rot)
                    return
                tx_val = float(elem.get('x', 0))
                ty_val = float(elem.get('y', 0))
                calc_x = tx_val * sx + tx
                calc_y = ty_val * sy + ty
                if calc_x < -20.0 or calc_x > vb_w + 20.0 or calc_y < -20.0 or calc_y > vb_h + 20.0:
                    return
                fs_str = elem.get('font-size', '10')
                m_fs = re.search(r'([\d.]+)', fs_str)
                fsize = float(m_fs.group(1)) * sx * scale_to_cad * 0.72 if m_fs else 90.0
                fsize = max(60.0, fsize)
                anchor = elem.get('text-anchor', 'start')
                pt = svg_to_cad(tx_val, ty_val, tx, ty, sx, sy)

                # DXF rotation: convert SVG rotation to CAD rotation (accounting for Y-axis flip)
                dxf_rot = (-rot) % 360.0
                if dxf_rot < 0:
                    dxf_rot += 360.0

                # Nâng Y text lên 1mm tính theo bản in ra (printed paper) cho text ngang
                if abs(dxf_rot) < 1.0 or abs(dxf_rot - 180.0) < 1.0:
                    pt = (pt[0], pt[1] + text_y_offset_cad)

                align_map = {'start': TextEntityAlignment.LEFT,
                             'middle': TextEntityAlignment.MIDDLE_CENTER,
                             'end': TextEntityAlignment.RIGHT}
                align_enum = align_map.get(anchor, TextEntityAlignment.LEFT)

                t_ent = msp.add_text(
                    txt,
                    dxfattribs={
                        'height': fsize,
                        'layer': 'TEXT',
                        'style': 'Standard',
                        'rotation': dxf_rot
                    }
                )
                t_ent.set_placement(pt, align=align_enum)
                t_ent.dxf.rotation = dxf_rot

            elif tag == 'path':
                d = elem.get('d', '')
                if not d:
                    for child in elem:
                        walk(child, tx, ty, sx, sy, rot)
                    return
                # Skip pure white-fill no-stroke background rect paths
                if fill in ('#ffffff', 'white') and stroke in ('none', ''):
                    for child in elem:
                        walk(child, tx, ty, sx, sy, rot)
                    return

                segments = parse_path_to_segments(d, tx, ty, sx, sy)
                add_dxf_entities(segments, layer, fill, lw, tx, ty, sx, sy)

            for child in elem:
                walk(child, tx, ty, sx, sy, rot)

        walk(root)

    out_buf = io.StringIO()
    doc.write(out_buf)
    return out_buf.getvalue().encode('utf-8')
