#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
beam_cad_exporter.py
Bộ xuất bản vẽ kỹ thuật dầm ETABS sang định dạng PDF và DXF (AutoCAD).
Quy chuẩn nét vẽ PDF (TCVN 5574-2012):
- Bản vẽ PDF ĐEN TRẮNG (Monochrome) thuần túy chuyên nghiệp:
  + Thép chủ và thép tăng cường: 0.50 mm (1.417 pt), nét đậm đen nổi bật
  + Bê tông viền dầm, cột đỡ, mặt cắt: 0.30 mm (0.850 pt)
  + Khung tên bản vẽ: 0.35 mm (0.992 pt)
  + Cốt đai, đường phân cách: 0.15 mm (0.425 pt)
  + Nét dim, gạch chéo tick, đường dóng, tim trục, leader: 0.09 mm (0.255 pt)
- Bố cục 1:1 đồng bộ tuyệt đối với màn hình:
  + Tiêu đề bản vẽ đặt ở ALIGN BOTTOM đáy khung bản vẽ.
  + Dầm dọc liên tục đa nhịp (Multi-span Elevation) ở nửa trên.
  + Toàn bộ hệ thống mặt cắt ngang (Cross sections 1-1, 2-2, 3-3, 4-4...) ở nửa dưới.
  + Đầy đủ móc neo bẻ 90° vào cột, móc neo thép tăng cường 45°, đai dầm, bóng số hiệu thép (1, 2, 5, 6).
  + Lưới trục kiến trúc (A, B, C... / 1, 2, 3...) và cột đỡ tại các gối có cột thật.
- DXF (AutoCAD R2010):
  + Tọa độ mm thực tế 1:1, khớp mẫu dim.dxf, font tahoma.ttf không bao giờ lỗi font tiếng Việt.
  + Đầy đủ các layer tiêu chuẩn: BE_TONG, THEP_CHU, THEP_TANG_CUONG, COT_DAI, DIM, TRUC, TEXT, KHUNG_TEN.
  + Bao gồm đầy đủ toàn bộ lưới mặt cắt (1-1 đến n-n) ở nửa dưới.
"""

import os
import io
import math
import json
import re
from reportlab.lib.pagesizes import A3, landscape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import ezdxf
from ezdxf.enums import TextEntityAlignment
from dxf_template_helper import get_template_dxf_doc, ensure_layer

# Đăng ký font TrueType Arial tiếng Việt
HAS_ARIAL = False
font_dir = "C:/Windows/Fonts"
if os.path.exists(os.path.join(font_dir, "arial.ttf")):
    try:
        pdfmetrics.registerFont(TTFont("Arial", os.path.join(font_dir, "arial.ttf")))
        pdfmetrics.registerFont(TTFont("Arial-Bold", os.path.join(font_dir, "arialbd.ttf")))
        HAS_ARIAL = True
    except Exception as e:
        print(f"[Exporter] Không thể đăng ký font Arial: {e}")

FONT_REGULAR = "Arial" if HAS_ARIAL else "Helvetica"
FONT_BOLD = "Arial-Bold" if HAS_ARIAL else "Helvetica-Bold"

# Hằng số quy đổi mm sang pt trong ReportLab (72 pt / inch, 1 inch = 25.4 mm)
MM_TO_PT = 72.0 / 25.4

# Chiều dày nét in PDF chuẩn TCVN
LW_REBAR_PT = 0.50 * MM_TO_PT    # 0.50 mm = 1.417 pt (Thép chủ & thép tăng cường - Đậm nhất)
LW_CONCRETE_PT = 0.30 * MM_TO_PT # 0.30 mm = 0.850 pt (Đường bao bê tông dầm, cột, mặt cắt)
LW_BORDER_PT = 0.35 * MM_TO_PT   # 0.35 mm = 0.992 pt (Khung bản vẽ)
LW_STIRRUP_PT = 0.15 * MM_TO_PT  # 0.15 mm = 0.425 pt (Cốt đai dầm & mặt cắt)
LW_DEFAULT_PT = 0.15 * MM_TO_PT  # 0.15 mm = 0.425 pt (Nét trung bình: khung trong, tim trục)
LW_DIM_PT = 0.09 * MM_TO_PT      # 0.09 mm = 0.255 pt (Nét mảnh: dim, leader, đường dóng)

# Màu đen trắng (Monochrome) thuần túy cho bản vẽ in ấn kỹ thuật
COLOR_BLACK = (0.0, 0.0, 0.0)
COLOR_DARK = (0.15, 0.15, 0.15)
COLOR_GRAY = (0.35, 0.35, 0.35)
COLOR_LIGHT_GRAY = (0.6, 0.6, 0.6)

# Kích thước khổ giấy A3 ngang
SHEET_W_MM = 420.0
SHEET_H_MM = 297.0
SHEET_W_PT = SHEET_W_MM * MM_TO_PT # 1190.55 pt
SHEET_H_PT = SHEET_H_MM * MM_TO_PT # 841.89 pt


def parse_rebar_spec(rebar_str, default_count=2, default_diam=18):
    """Bóc tách quy cách thép (ví dụ: '2D18', '2D22+1D20', '3D20')."""
    if not rebar_str:
        return {"count": default_count, "diam": default_diam, "extra_count": 0, "extra_diam": 0, "label": f"{default_count}Φ{default_diam}"}
    
    clean = rebar_str.split('(')[0].strip()
    matches = list(re.finditer(r'(\d+)\s*[dDΦØøϕ]\s*(\d+)', clean))
    if len(matches) >= 2:
        c1, d1 = int(matches[0].group(1)), int(matches[0].group(2))
        c2, d2 = int(matches[1].group(1)), int(matches[1].group(2))
        return {"count": c1, "diam": d1, "extra_count": c2, "extra_diam": d2, "label": f"{c1}Φ{d1}+{c2}Φ{d2}"}
    elif len(matches) == 1:
        c1, d1 = int(matches[0].group(1)), int(matches[0].group(2))
        return {"count": c1, "diam": d1, "extra_count": 0, "extra_diam": 0, "label": f"{c1}Φ{d1}"}
    
    return {"count": default_count, "diam": default_diam, "extra_count": 0, "extra_diam": 0, "label": clean or f"{default_count}Φ{default_diam}"}


def format_story_name(story):
    if not story:
        return ""
    s = str(story).strip()
    if s.upper() in ["DK", "DA KIENG", "ĐÀ KIỀNG"]:
        return "ĐÀ KIỀNG"
    if s.upper().startswith("T") and s[1:].isdigit():
        return f"TẦNG {s[1:]}"
    if s.upper().startswith("STORY") and s[5:].isdigit():
        return f"TẦNG {s[5:]}"
    if s.upper().startswith("TẦNG"):
        return s.upper()
    return f"TẦNG {s}"


def is_short_beam(beam_group):
    """Kiểm tra dầm có phải là dầm ngắn (< 1/2 trang in A3) hay không."""
    num_spans = len(beam_group.get("beams", []))
    tot_len = beam_group.get("total_length_mm", 0) or sum(b.get("length", 0) for b in beam_group.get("beams", []))
    return (num_spans <= 2 and tot_len <= 12000) or (num_spans == 1 and tot_len <= 15000)


def get_etabs_context(etabs_data=None):
    """Lấy dữ liệu phụ trợ cột và lưới trục ETABS."""
    if etabs_data is None:
        try:
            import etabs_service
            etabs_data = etabs_service.get_etabs_data()
        except Exception:
            etabs_data = {}
    return {
        "columns": etabs_data.get("columns", []),
        "grids": etabs_data.get("grids", {})
    }


def check_column_at_support(chain, support_idx, is_x, columns):
    """Kiểm tra xem tại gối support_idx có cột thực sự trong mô hình hay không."""
    if not chain or not columns:
        return True
    num_spans = len(chain)
    if support_idx < num_spans:
        b = chain[support_idx]
        p1 = b.get('p1') or [0, 0]
        p2 = b.get('p2') or [0, 0]
        if is_x:
            xj = min(p1[0], p2[0])
            yj = (p1[1] + p2[1]) / 2.0
        else:
            xj = (p1[0] + p2[0]) / 2.0
            yj = min(p1[1], p2[1])
    else:
        b = chain[num_spans - 1]
        p1 = b.get('p1') or [0, 0]
        p2 = b.get('p2') or [0, 0]
        if is_x:
            xj = max(p1[0], p2[0])
            yj = (p1[1] + p2[1]) / 2.0
        else:
            xj = (p1[0] + p2[0]) / 2.0
            yj = max(p1[1], p2[1])

    tol = 450
    for c in columns:
        cp = c.get('p1') or [c.get('x', 0), c.get('y', 0)]
        if math.hypot(cp[0] - xj, cp[1] - yj) <= tol:
            return True
    return False


def get_grid_bubble_label(coord, is_x, grids):
    """Lấy tên trục kiến trúc gần tọa độ gối nhất."""
    if not grids:
        return None
    grid_list = grids.get('X' if is_x else 'Y', [])
    min_dist = 500
    matched = None
    for g in grid_list:
        d = abs(g.get('ordinate', 0) - coord)
        if d <= min_dist:
            min_dist = d
            matched = g.get('id')
    return matched


def get_beam_groups_from_data(etabs_data=None, story_filter=None, beam_id_filter=None):
    """Trích xuất và gom nhóm các dầm dài liên tục từ dữ liệu ETABS."""
    if etabs_data is None:
        try:
            import etabs_service
            etabs_data = etabs_service.get_etabs_data()
        except Exception:
            etabs_data = {}
    
    beams = etabs_data.get("beams", [])
    groups = {}
    for b in beams:
        st = b.get("story", "T1")
        l_id = b.get("long_beam_id") or b.get("label", "BEAM")
        if story_filter and st != story_filter:
            continue
        if beam_id_filter and l_id != beam_id_filter:
            continue
        key = (st, l_id)
        if key not in groups:
            groups[key] = {
                "story": st,
                "long_beam_id": l_id,
                "beams": [],
                "commonSection": b.get("section", "200x400"),
                "total_length_mm": 0,
                "axisName": b.get("axisName", ""),
                "direction": b.get("direction", "X"),
                "rebar_main_top": b.get("rebar_main_top", "2D18"),
                "rebar_main_bot": b.get("rebar_main_bot", "2D18"),
                "rebar_top_left": b.get("rebar_top_left", "2D18"),
                "rebar_bot_mid": b.get("rebar_bot_mid", "2D18"),
                "rebar_top_right": b.get("rebar_top_right", "2D18"),
                "rebar_hanger": b.get("rebar_hanger", "2D16"),
                "stirrup": b.get("stirrup", "d6a100/a200")
            }
        groups[key]["beams"].append(b)

    result = []
    for (st, l_id), g in groups.items():
        g["beams"].sort(key=lambda x: x.get("span_index", 0))
        g["total_length_mm"] = sum(b.get("length", 0) for b in g["beams"])
        result.append(g)

    result.sort(key=lambda x: (x["story"], x["long_beam_id"]))
    return result


def parse_page_range(range_str, max_pages):
    """Phân tích chuỗi khoảng trang như '1-3, 5' thành danh sách số nguyên 1-based."""
    if not range_str or str(range_str).strip().lower() == 'all':
        return list(range(1, max_pages + 1))
    pages = set()
    parts = [p.strip() for p in str(range_str).split(',') if p.strip()]
    for p in parts:
        if '-' in p:
            sub = p.split('-')
            if len(sub) == 2 and sub[0].strip().isdigit() and sub[1].strip().isdigit():
                start = int(sub[0].strip())
                end = int(sub[1].strip())
                if start > end:
                    start, end = end, start
                for pg in range(start, end + 1):
                    if 1 <= pg <= max_pages:
                        pages.add(pg)
        elif p.isdigit():
            pg = int(p)
            if 1 <= pg <= max_pages:
                pages.add(pg)
    return sorted(list(pages)) if pages else list(range(1, max_pages + 1))


def build_pages_list(beam_groups, combine_short=True):
    """Gom nhóm danh sách dầm thành danh sách các trang in (A3)."""
    pages = []
    if combine_short:
        i = 0
        while i < len(beam_groups):
            bg1 = beam_groups[i]
            if is_short_beam(bg1) and (i + 1 < len(beam_groups)) and is_short_beam(beam_groups[i+1]):
                bg2 = beam_groups[i+1]
                pages.append({"type": "combined", "beams": [bg1, bg2]})
                i += 2
            else:
                pages.append({"type": "single", "beams": [bg1]})
                i += 1
    else:
        for bg in beam_groups:
            pages.append({"type": "single", "beams": [bg]})
    return pages


# ==============================================================================
# REPORTLAB PDF GENERATION (CHUẨN ĐEN TRẮNG MONOCHROME 1:1)
# ==============================================================================

def generate_beam_pdf(beam_groups, combine_short=True, layout_settings=None, page_scope='all', page_range=None, current_page_index=1):
    """Tạo file PDF bản vẽ dầm A3 đạt chuẩn nét vẽ đen trắng TCVN 5574-2012."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A3))
    
    all_pages = build_pages_list(beam_groups, combine_short=combine_short)
    if not all_pages:
        return b""

    total_doc_pages = len(all_pages)

    if page_scope == 'current':
        idx = max(1, min(int(current_page_index or 1), total_doc_pages))
        selected_indices = [idx]
    elif page_scope == 'range' and page_range:
        if isinstance(page_range, str):
            selected_indices = parse_page_range(page_range, total_doc_pages)
        else:
            selected_indices = [i for i in page_range if 1 <= i <= total_doc_pages]
        if not selected_indices:
            selected_indices = list(range(1, total_doc_pages + 1))
    else:
        selected_indices = list(range(1, total_doc_pages + 1))

    ctx_data = get_etabs_context()

    for p_out_idx, orig_page_num in enumerate(selected_indices):
        page_info = all_pages[orig_page_num - 1]
        draw_pdf_page(c, page_info, orig_page_num, total_doc_pages, layout_settings, ctx_data)
        c.showPage()

    c.save()
    buffer.seek(0)
    return buffer.getvalue()


def draw_pdf_page(c, page_info, page_num, total_pages, layout_settings=None, ctx_data=None):
    """Vẽ 1 trang A3 (chứa 1 dầm dài hoặc 2 dầm ngắn kết hợp) chuẩn đen trắng."""
    margin_page_pt = 12.0 * MM_TO_PT # 12mm lề giấy A3
    frame_x = margin_page_pt
    frame_y = margin_page_pt
    frame_w = SHEET_W_PT - margin_page_pt * 2
    frame_h = SHEET_H_PT - margin_page_pt * 2

    c.saveState()
    # 1. Khung bản vẽ A3 ngoài cùng (0.35 mm)
    c.setLineWidth(LW_BORDER_PT)
    c.setStrokeColorRGB(*COLOR_BLACK)
    c.rect(frame_x, frame_y, frame_w, frame_h)
    
    # 2. Khung viền đôi trong (0.15 mm)
    c.setLineWidth(LW_DEFAULT_PT)
    c.rect(frame_x + 5, frame_y + 5, frame_w - 10, frame_h - 10)
    c.restoreState()

    beams = page_info["beams"]
    if len(beams) == 1:
        draw_single_beam_pdf(c, beams[0], frame_x + 8, frame_y + 8, frame_w - 16, frame_h - 16, page_num=page_num, total_pages=total_pages, is_half=False, ctx_data=ctx_data)
    else:
        half_h = (frame_h - 20) / 2.0
        # Dầm 1 ở nửa trên
        draw_single_beam_pdf(c, beams[0], frame_x + 8, frame_y + half_h + 10, frame_w - 16, half_h - 10, page_num=page_num, total_pages=total_pages, is_half=True, beam_sub_title="NỬA TRÊN", ctx_data=ctx_data)
        
        # Đường nét đứt phân cách giữa 2 dầm
        c.saveState()
        c.setLineWidth(LW_DEFAULT_PT)
        c.setStrokeColorRGB(*COLOR_GRAY)
        c.setDash(4, 4)
        c.line(frame_x + 12, frame_y + half_h + 5, frame_x + frame_w - 12, frame_y + half_h + 5)
        c.restoreState()

        # Dầm 2 ở nửa dưới
        draw_single_beam_pdf(c, beams[1], frame_x + 8, frame_y + 8, frame_w - 16, half_h - 10, page_num=page_num, total_pages=total_pages, is_half=True, beam_sub_title="NỬA DƯỚI", ctx_data=ctx_data)


def draw_single_beam_pdf(c, bg, bx, by, bw, bh, page_num=1, total_pages=1, is_half=False, beam_sub_title="", ctx_data=None):
    """Vẽ chi tiết 1 dầm: Title ở ĐÁY (align bottom), Elevation ở trên, Grid mặt cắt ở dưới."""
    spans = bg.get("beams", [])
    if not spans:
        return

    long_id = bg.get("long_beam_id", spans[0].get("label", "BEAM"))
    story = bg.get("story", spans[0].get("story", "T1"))
    sec = bg.get("commonSection", spans[0].get("section", "200x400"))
    num_spans = len(spans)
    tot_len = sum(b.get("length", 4000) for b in spans)
    if tot_len <= 0:
        tot_len = 6000

    # Xác định phương X hay Y
    is_x = True
    if spans and spans[0].get("direction"):
        is_x = (spans[0].get("direction") == 'X')
    elif spans and spans[0].get("p1") and spans[0].get("p2"):
        dx = abs(spans[0]["p2"][0] - spans[0]["p1"][0])
        dy = abs(spans[0]["p2"][1] - spans[0]["p1"][1])
        is_x = (dx >= dy)

    columns = ctx_data.get("columns", []) if ctx_data else []
    grids = ctx_data.get("grids", {}) if ctx_data else {}

    # Kiểm tra cột và lưới trục tại từng gối
    has_col = [check_column_at_support(spans, i, is_x, columns) for i in range(num_spans + 1)]
    support_coords = []
    for i in range(num_spans):
        b = spans[i]
        p1 = b.get("p1", [0, 0])
        p2 = b.get("p2", [0, 0])
        support_coords.append(min(p1[0 if is_x else 1], p2[0 if is_x else 1]))
    last_b = spans[-1]
    last_p1 = last_b.get("p1", [0, 0])
    last_p2 = last_b.get("p2", [0, 0])
    support_coords.append(max(last_p1[0 if is_x else 1], last_p2[0 if is_x else 1]))
    grid_labels = [get_grid_bubble_label(coord, is_x, grids) for coord in support_coords]

    # ==============================================================================
    # 1. TIÊU ĐỀ BẢN VẼ DẦM: ĐƯA XUỐNG ALIGN BOTTOM TRANG IN
    # ==============================================================================
    c.saveState()
    story_str = format_story_name(story)
    axis_name = bg.get("axisName") or spans[0].get("axisName") or ""
    axis_part = f" • TRỤC {axis_name.replace('Trục ', '').strip().upper()}" if axis_name else ""
    clean_sec = re.sub(r'^[bB]\s*', '', sec).strip()
    title_text = f"BẢN VẼ CHI TIẾT DẦM: {long_id} • {story_str}{axis_part} ({num_spans} NHỊP • {clean_sec})"
    if beam_sub_title:
        title_text += f" [{beam_sub_title}]"

    # Đặt ở đáy khung (align bottom)
    c.setFont(FONT_BOLD, 10 if not is_half else 9)
    c.setFillColorRGB(*COLOR_BLACK)
    c.drawCentredString(bx + bw / 2.0, by + 12, title_text)

    # Thông tin chú thích 2 bên đáy
    c.setFont(FONT_REGULAR, 7.5 if not is_half else 7)
    c.setFillColorRGB(*COLOR_GRAY)
    c.drawString(bx + 12, by + 12, "REVITAI STRUCTURAL CAD • TCVN 5574-2012")
    c.drawRightString(bx + bw - 12, by + 12, f"KHỔ GIẤY A3 • TỶ LỆ 1/50 • TRANG {page_num}/{total_pages}")
    c.restoreState()

    # ==============================================================================
    # 2. PHÂN CHIA VÙNG: NỬA TRÊN CHO ELEVATION, NỬA DƯỚI CHO CROSS SECTIONS
    # ==============================================================================
    margin_x = 45.0
    drawable_w = bw - margin_x * 2.0
    scale_x = drawable_w / tot_len

    # Chiều cao dành cho Elevation và Cross Sections
    elev_h = bh * (0.50 if not is_half else 0.46)
    elev_y = by + bh - elev_h - 10
    cs_y = by + 28
    cs_h = elev_y - cs_y - 12

    # Đường phân cách nét đứt giữa Elevation và Mặt cắt
    c.saveState()
    c.setLineWidth(LW_STIRRUP_PT)
    c.setStrokeColorRGB(*COLOR_LIGHT_GRAY)
    c.setDash(4, 4)
    c.line(bx + 15, elev_y - 8, bx + bw - 15, elev_y - 8)
    c.restoreState()

    # ==============================================================================
    # 3. VẼ DẦM DỌC LIÊN TỤC (ELEVATION)
    # ==============================================================================
    beam_draw_h = min(36.0, max(20.0, spans[0].get("depth", 400) * 0.065))
    beam_top_y = elev_y + elev_h * 0.60
    beam_bot_y = beam_top_y - beam_draw_h

    cur_x = bx + margin_x
    span_coords = []
    for b in spans:
        s_len = b.get("length", 4000)
        s_w = s_len * scale_x
        s_depth = b.get("depth", 400)
        s_draw_h = min(36.0, max(20.0, s_depth * 0.065))
        s_bot_y = beam_top_y - s_draw_h

        # Khung bê tông dầm (Nét 0.30 mm, màu đen)
        c.saveState()
        c.setLineWidth(LW_CONCRETE_PT)
        c.setStrokeColorRGB(*COLOR_BLACK)
        c.rect(cur_x, s_bot_y, s_w, s_draw_h)
        c.restoreState()

        span_coords.append({
            "beam": b,
            "x1": cur_x,
            "x2": cur_x + s_w,
            "w": s_w,
            "len": s_len,
            "depth": s_depth,
            "draw_h": s_draw_h,
            "bot_y": s_bot_y
        })
        cur_x += s_w

    start_x = span_coords[0]["x1"]
    end_x = span_coords[-1]["x2"]

    # Cột đỡ tại các gối (chỉ vẽ khi has_col[i] là True)
    col_w_pt = max(14.0, 350.0 * scale_x)
    col_h_pt = 20.0
    c.saveState()
    c.setLineWidth(LW_CONCRETE_PT)
    c.setStrokeColorRGB(*COLOR_BLACK)
    for i, sc in enumerate(span_coords):
        if has_col[i]:
            c.rect(sc["x1"] - col_w_pt/2.0, sc["bot_y"] - col_h_pt, col_w_pt, col_h_pt)
            # Nét gạch chéo thể hiện cột bê tông
            c.saveState()
            c.setLineWidth(LW_DIM_PT)
            c.setStrokeColorRGB(*COLOR_LIGHT_GRAY)
            c.line(sc["x1"] - col_w_pt/2.0, sc["bot_y"] - col_h_pt, sc["x1"] + col_w_pt/2.0, sc["bot_y"])
            c.restoreState()
        if i == len(span_coords) - 1 and has_col[i + 1]:
            c.rect(sc["x2"] - col_w_pt/2.0, sc["bot_y"] - col_h_pt, col_w_pt, col_h_pt)
            c.saveState()
            c.setLineWidth(LW_DIM_PT)
            c.setStrokeColorRGB(*COLOR_LIGHT_GRAY)
            c.line(sc["x2"] - col_w_pt/2.0, sc["bot_y"] - col_h_pt, sc["x2"] + col_w_pt/2.0, sc["bot_y"])
            c.restoreState()
    c.restoreState()

    # Cốt đai trong thân dầm dọc (Nét 0.15 mm đen)
    c.saveState()
    c.setLineWidth(LW_STIRRUP_PT)
    c.setStrokeColorRGB(*COLOR_DARK)
    for sc in span_coords:
        st_x1 = sc["x1"] + 3
        st_x2 = sc["x2"] - 3
        q = sc["w"] * 0.25
        step_dense = max(2.5, q / 6.0)
        cx = st_x1
        while cx <= st_x1 + q:
            c.line(cx, sc["bot_y"] + 2, cx, beam_top_y - 2)
            cx += step_dense
        step_mid = step_dense * 2.0
        while cx <= st_x2 - q:
            c.line(cx, sc["bot_y"] + 2, cx, beam_top_y - 2)
            cx += step_mid
        while cx <= st_x2:
            c.line(cx, sc["bot_y"] + 2, cx, beam_top_y - 2)
            cx += step_dense
    c.restoreState()

    # CỐT THÉP DỌC DẦM: ĐẬM NÉT 0.50 MM (Màu đen thuần túy)
    c.saveState()
    c.setLineWidth(LW_REBAR_PT)
    c.setStrokeColorRGB(*COLOR_BLACK)

    # 1. Thép chủ trên (suốt tuyến dầm)
    top_y = beam_top_y - 3.5
    c.line(start_x + 3, top_y, end_x - 3, top_y)
    # Móc neo bẻ 90° chúc xuống hết chiều cao dầm và mỏ bẻ xéo 45° vào trong
    hook_l_h = span_coords[0]["draw_h"] - 7
    hook_r_h = span_coords[-1]["draw_h"] - 7
    c.line(start_x + 3, top_y, start_x + 3, top_y - hook_l_h)
    c.line(start_x + 3, top_y - hook_l_h, start_x + 7, top_y - hook_l_h + 4)
    c.line(end_x - 3, top_y, end_x - 3, top_y - hook_r_h)
    c.line(end_x - 3, top_y - hook_r_h, end_x - 7, top_y - hook_r_h + 4)

    # 2. Thép chủ dưới (suốt tuyến dầm)
    bot_y0 = span_coords[0]["bot_y"] + 3.5
    bot_y_end = span_coords[-1]["bot_y"] + 3.5
    for i, sc in enumerate(span_coords):
        by_cur = sc["bot_y"] + 3.5
        c.line(sc["x1"] + 3, by_cur, sc["x2"] - 3, by_cur)
        if i < len(span_coords) - 1:
            by_next = span_coords[i+1]["bot_y"] + 3.5
            c.line(sc["x2"] - 3, by_cur, sc["x2"] + 3, by_next)
    # Móc neo bẻ lên ở 2 đầu
    c.line(start_x + 3, bot_y0, start_x + 3, bot_y0 + 10)
    c.line(start_x + 3, bot_y0 + 10, start_x + 7, bot_y0 + 10 - 4)
    c.line(end_x - 3, bot_y_end, end_x - 3, bot_y_end + 10)
    c.line(end_x - 3, bot_y_end + 10, end_x - 7, bot_y_end + 10 - 4)

    # 3. Thép tăng cường gối trên (0.25L gối)
    top_extra_y = top_y - 3.5
    for i, sc in enumerate(span_coords):
        l_quarter = sc["w"] * 0.25
        if i == 0:
            c.line(sc["x1"] + 3, top_extra_y, sc["x1"] + l_quarter, top_extra_y)
            c.line(sc["x1"] + 3, top_extra_y, sc["x1"] + 3, top_extra_y - 6)
            c.line(sc["x1"] + l_quarter, top_extra_y, sc["x1"] + l_quarter - 4, top_extra_y - 3)
        if i < len(span_coords) - 1:
            next_q = span_coords[i+1]["w"] * 0.25
            c.line(sc["x2"] - l_quarter, top_extra_y, sc["x2"] + next_q, top_extra_y)
            c.line(sc["x2"] - l_quarter, top_extra_y, sc["x2"] - l_quarter + 4, top_extra_y - 3)
            c.line(sc["x2"] + next_q, top_extra_y, sc["x2"] + next_q - 4, top_extra_y - 3)
        else:
            c.line(sc["x2"] - l_quarter, top_extra_y, sc["x2"] - 3, top_extra_y)
            c.line(sc["x2"] - l_quarter, top_extra_y, sc["x2"] - l_quarter + 4, top_extra_y - 3)
            c.line(sc["x2"] - 3, top_extra_y, sc["x2"] - 3, top_extra_y - 6)

    # 4. Thép tăng cường bụng dưới (0.15L đến 0.85L)
    for sc in span_coords:
        if sc["len"] >= 2000:
            cut_l = sc["w"] * 0.15
            cut_r = sc["w"] * 0.85
            bot_extra_y = sc["bot_y"] + 7.0
            c.line(sc["x1"] + cut_l, bot_extra_y, sc["x1"] + cut_r, bot_extra_y)
            c.line(sc["x1"] + cut_l, bot_extra_y, sc["x1"] + cut_l + 4, bot_extra_y + 3)
            c.line(sc["x1"] + cut_r, bot_extra_y, sc["x1"] + cut_r - 4, bot_extra_y + 3)
    c.restoreState()

    # KÍCH THƯỚC (DIM): NÉT MẢNH 0.09 MM (Màu đen/xám)
    c.saveState()
    c.setLineWidth(LW_DIM_PT)
    c.setStrokeColorRGB(*COLOR_BLACK)
    c.setFillColorRGB(*COLOR_BLACK)
    c.setFont(FONT_REGULAR, 6.0)

    # A. Dim chuỗi phía trên dầm
    dim_top_y = beam_top_y + 14.0
    for sc in span_coords:
        q = sc["w"] * 0.25
        dense_str = f"{int(sc['len']*0.25)}"
        mid_str = f"{int(sc['len']*0.50)}"
        draw_pdf_dim_line(c, sc["x1"], dim_top_y, sc["x1"] + q, dim_top_y, dense_str)
        draw_pdf_dim_line(c, sc["x1"] + q, dim_top_y, sc["x2"] - q, dim_top_y, mid_str)
        draw_pdf_dim_line(c, sc["x2"] - q, dim_top_y, sc["x2"], dim_top_y, dense_str)

    # B. Dim cắt thép tăng cường bụng bên dưới
    min_bot_y = min(sc["bot_y"] for sc in span_coords)
    dim_cut_y = min_bot_y - 13.0
    for sc in span_coords:
        if sc["len"] >= 2000:
            len_val = sc["len"]
            len_l = int(len_val * 0.15)
            len_m = int(len_val * 0.70)
            len_r = int(len_val) - len_l - len_m
            x_a = sc["x1"]
            x_b = sc["x1"] + sc["w"] * 0.15
            x_c = sc["x1"] + sc["w"] * 0.85
            x_d = sc["x2"]
            draw_pdf_dim_line(c, x_a, dim_cut_y, x_b, dim_cut_y, f"{len_l}")
            draw_pdf_dim_line(c, x_b, dim_cut_y, x_c, dim_cut_y, f"{len_m}")
            draw_pdf_dim_line(c, x_c, dim_cut_y, x_d, dim_cut_y, f"{len_r}")

    # C. Dim nhịp thông thủy
    dim_span_y = dim_cut_y - 13.0
    for sc in span_coords:
        draw_pdf_dim_line(c, sc["x1"], dim_span_y, sc["x2"], dim_span_y, f"{int(sc['len'])}")

    # D. Dim tổng chiều dài dầm
    dim_total_y = dim_span_y - 13.0
    draw_pdf_dim_line(c, start_x, dim_total_y, end_x, dim_total_y, f"{int(tot_len)}", is_bold=True)
    c.restoreState()

    # Ký hiệu trục tròn và đường tim trục
    bubble_y_top = dim_top_y + 16.0
    bubble_y_bot = dim_total_y - 14.0
    c.saveState()
    c.setLineWidth(LW_DEFAULT_PT)
    c.setStrokeColorRGB(*COLOR_BLACK)
    c.setFont(FONT_BOLD, 6.5)
    c.setFillColorRGB(*COLOR_BLACK)

    for i in range(num_spans + 1):
        if not has_col[i]:
            continue
        x_col = span_coords[i]["x1"] if i < num_spans else span_coords[-1]["x2"]
        lbl = grid_labels[i] or f"{i+1}"
        
        # Đường tim trục nét đứt xuyên suốt cột
        c.saveState()
        c.setLineWidth(LW_DIM_PT)
        c.setStrokeColorRGB(*COLOR_GRAY)
        c.setDash(4, 2)
        c.line(x_col, bubble_y_top - 6.5, x_col, bubble_y_bot + 6.5)
        c.restoreState()

        # Bong bóng trục trên
        c.circle(x_col, bubble_y_top, 6.0)
        c.drawCentredString(x_col, bubble_y_top - 2.5, lbl)

        # Bong bóng trục dưới
        c.circle(x_col, bubble_y_bot, 6.0)
        c.drawCentredString(x_col, bubble_y_bot - 2.5, lbl)
    c.restoreState()

    # Dấu mặt cắt kỹ thuật trên dầm dọc (1-1, 2-2, 3-3, 4-4...)
    cut_counter = 1
    c.saveState()
    c.setFont(FONT_BOLD, 6.0)
    c.setFillColorRGB(*COLOR_BLACK)
    c.setStrokeColorRGB(*COLOR_BLACK)
    c.setLineWidth(LW_STIRRUP_PT)

    all_cross_sections = []
    for s_idx, sc in enumerate(span_coords):
        span_l = sc["len"]
        b = sc["beam"]
        w = b.get("width", 200)
        h = b.get("depth", 400)
        reb_main_top = parse_rebar_spec(b.get("rebar_main_top") or bg.get("rebar_main_top", "2D18"))
        reb_main_bot = parse_rebar_spec(b.get("rebar_main_bot") or bg.get("rebar_main_bot", "2D18"))
        reb_top_l = parse_rebar_spec(b.get("extra_top_left") or b.get("rebar_top_left"))
        reb_bot_m = parse_rebar_spec(b.get("extra_bot_mid") or b.get("rebar_bot_mid"))
        reb_top_r = parse_rebar_spec(b.get("extra_top_right") or b.get("rebar_top_right"))
        st_spec = b.get("stirrup", "d6a100/a200")

        if span_l < 2000:
            idx = cut_counter
            cut_counter += 1
            x_cut = sc["x1"] + sc["w"] * 0.50
            draw_pdf_cut_symbol(c, x_cut, str(idx), beam_top_y + 8, sc["bot_y"] - 3)
            all_cross_sections.append({
                "title": f"{idx}-{idx}",
                "sub": f"Nhịp {s_idx+1}",
                "w": w, "h": h,
                "top_main": reb_main_top,
                "top_extra": reb_top_l if reb_top_l["count"] > 0 else None,
                "bot_main": reb_main_bot,
                "bot_extra": None,
                "stirrup": "d6a100",
                "is_deep": (h >= 700)
            })
        else:
            idx1, idx2, idx3 = cut_counter, cut_counter + 1, cut_counter + 2
            cut_counter += 3
            draw_pdf_cut_symbol(c, sc["x1"] + sc["w"] * 0.12, str(idx1), beam_top_y + 8, sc["bot_y"] - 3)
            draw_pdf_cut_symbol(c, sc["x1"] + sc["w"] * 0.50, str(idx2), beam_top_y + 8, sc["bot_y"] - 3)
            draw_pdf_cut_symbol(c, sc["x2"] - sc["w"] * 0.12, str(idx3), beam_top_y + 8, sc["bot_y"] - 3)
            
            all_cross_sections.append({
                "title": f"{idx1}-{idx1}",
                "sub": f"Gối T (N{s_idx+1})",
                "w": w, "h": h,
                "top_main": reb_main_top,
                "top_extra": reb_top_l if reb_top_l["count"] > 0 else None,
                "bot_main": reb_main_bot,
                "bot_extra": None,
                "stirrup": "d6a100",
                "is_deep": (h >= 700)
            })
            all_cross_sections.append({
                "title": f"{idx2}-{idx2}",
                "sub": f"Bụng (N{s_idx+1})",
                "w": w, "h": h,
                "top_main": reb_main_top,
                "top_extra": None,
                "bot_main": reb_main_bot,
                "bot_extra": reb_bot_m if reb_bot_m["count"] > 0 else None,
                "stirrup": "d6a200",
                "is_deep": (h >= 700)
            })
            all_cross_sections.append({
                "title": f"{idx3}-{idx3}",
                "sub": f"Gối P (N{s_idx+1})",
                "w": w, "h": h,
                "top_main": reb_main_top,
                "top_extra": reb_top_r if reb_top_r["count"] > 0 else None,
                "bot_main": reb_main_bot,
                "bot_extra": None,
                "stirrup": "d6a100",
                "is_deep": (h >= 700)
            })
    c.restoreState()

    # ==============================================================================
    # 4. VẼ TOÀN BỘ HỆ THỐNG MẶT CẮT (CROSS SECTIONS) NỬA DƯỚI BẢN VẼ
    # ==============================================================================
    draw_cross_sections_pdf(c, all_cross_sections, bx + margin_x, cs_y, drawable_w, cs_h)


def draw_pdf_dim_line(c, x1, y1, x2, y2, text, is_bold=False):
    """Vẽ đường kích thước kèm gạch chéo 45 độ chuẩn CAD (Nét 0.09 mm)."""
    c.line(x1, y1, x2, y2)
    tick = 2.0
    c.line(x1 - tick, y1 - tick, x1 + tick, y1 + tick)
    c.line(x2 - tick, y2 - tick, x2 + tick, y2 + tick)
    c.line(x1, y1 - 2, x1, y1 + 2)
    c.line(x2, y2 - 2, x2, y2 + 2)
    if is_bold:
        c.setFont(FONT_BOLD, 6.5)
    c.drawCentredString((x1 + x2) / 2.0, y1 + 2.0, str(text))
    if is_bold:
        c.setFont(FONT_REGULAR, 6.0)


def draw_pdf_cut_symbol(c, x, label, y_top, y_bot):
    """Vẽ ký hiệu mặt cắt kỹ thuật (mũi tên chỉ hướng nhìn và số hiệu)."""
    c.line(x, y_top, x, y_bot)
    # Mũi tên nhìn sang phải tại đỉnh
    c.line(x, y_top, x + 5, y_top)
    c.line(x + 5, y_top, x + 2.5, y_top - 2.5)
    c.drawCentredString(x + 9, y_top - 1.5, label)
    # Mũi tên nhìn sang phải tại đáy
    c.line(x, y_bot, x + 5, y_bot)
    c.line(x + 5, y_bot, x + 2.5, y_bot + 2.5)
    c.drawCentredString(x + 9, y_bot + 1.5, label)


def draw_cross_sections_pdf(c, all_sections, cx, cy, cw, ch):
    """Vẽ toàn bộ các mặt cắt ngang trong lưới cột/hàng đạt chuẩn đen trắng."""
    num_cs = len(all_sections)
    if num_cs == 0:
        return

    cols_per_row = min(6, num_cs)
    num_rows = math.ceil(num_cs / cols_per_row)

    col_w = cw / cols_per_row
    row_h = ch / num_rows

    for idx, cs in enumerate(all_sections):
        row = idx // cols_per_row
        col = idx % cols_per_row

        x_cell = cx + col * col_w
        # Thứ tự từ hàng trên xuống hàng dưới
        y_cell = cy + (num_rows - 1 - row) * row_h

        draw_single_cross_section_pdf(c, cs, x_cell, y_cell, col_w, row_h)


def draw_single_cross_section_pdf(c, cs, x, y, w, h):
    """Vẽ 1 mặt cắt ngang: Bê tông 0.30mm, Đai 0.15mm, Thép tròn đen 0.50mm, Leader, Dim, Title."""
    b_width = cs["w"]
    b_depth = cs["h"]

    # Tỷ lệ co giãn mặt cắt sao cho vừa ô
    sw = min(28.0, max(18.0, col_w_factor := w * 0.28))
    sh = sw * (b_depth / max(1, b_width))
    if sh > h * 0.55:
        ratio = (h * 0.55) / sh
        sw *= ratio
        sh *= ratio

    sec_center_x = x + w / 2.0
    sec_bot_y = y + 26.0
    sec_top_y = sec_bot_y + sh
    sec_left_x = sec_center_x - sw / 2.0
    sec_right_x = sec_center_x + sw / 2.0

    c.saveState()

    # 1. Khung bê tông dầm (Nét 0.30 mm, màu đen)
    c.setLineWidth(LW_CONCRETE_PT)
    c.setStrokeColorRGB(*COLOR_BLACK)
    c.rect(sec_left_x, sec_bot_y, sw, sh)

    # 2. Cốt đai (Nét 0.15 mm, cách mép 2.5pt đại diện 25mm bê tông bảo vệ)
    cover = 2.5
    st_x1 = sec_left_x + cover
    st_y1 = sec_bot_y + cover
    st_x2 = sec_right_x - cover
    st_y2 = sec_top_y - cover
    c.setLineWidth(LW_STIRRUP_PT)
    c.setStrokeColorRGB(*COLOR_DARK)
    c.rect(st_x1, st_y1, st_x2 - st_x1, st_y2 - st_y1)
    # 2 móc bẻ xéo 135° ở góc trên trái
    c.line(st_x1 + 4, st_y2 - 4, st_x1 + 1, st_y2 - 1)
    c.line(st_x1 + 6, st_y2 - 4, st_x1 + 2.5, st_y2 - 1)

    # 3. Cốt thép tròn: Đậm đen 0.50 mm (Đặc ruột)
    dot_r = 1.8
    c.setFillColorRGB(*COLOR_BLACK)
    c.setStrokeColorRGB(*COLOR_BLACK)

    # Thép chủ trên (Top Layer 1)
    n_top = cs["top_main"]["count"]
    if n_top == 1:
        c.circle((st_x1 + st_x2) / 2.0, st_y2 - dot_r - 0.5, dot_r, stroke=1, fill=1)
    else:
        step = (st_x2 - st_x1 - dot_r * 2) / (n_top - 1)
        for i in range(n_top):
            c.circle(st_x1 + dot_r + i * step, st_y2 - dot_r - 0.5, dot_r, stroke=1, fill=1)

    # Thép tăng cường gối trên (Top Layer 2 - 2 góc biên)
    if cs.get("top_extra"):
        top_y2 = st_y2 - dot_r * 2 - 3.5
        c.circle(st_x1 + dot_r, top_y2, dot_r, stroke=1, fill=1)
        c.circle(st_x2 - dot_r, top_y2, dot_r, stroke=1, fill=1)

    # Thép chủ dưới (Bot Layer 1)
    n_bot = cs["bot_main"]["count"]
    if n_bot == 1:
        c.circle((st_x1 + st_x2) / 2.0, st_y1 + dot_r + 0.5, dot_r, stroke=1, fill=1)
    else:
        step = (st_x2 - st_x1 - dot_r * 2) / (n_bot - 1)
        for i in range(n_bot):
            c.circle(st_x1 + dot_r + i * step, st_y1 + dot_r + 0.5, dot_r, stroke=1, fill=1)

    # Thép tăng cường bụng dưới (Bot Layer 2 - 2 góc biên)
    if cs.get("bot_extra"):
        bot_y2 = st_y1 + dot_r * 2 + 3.5
        c.circle(st_x1 + dot_r, bot_y2, dot_r, stroke=1, fill=1)
        c.circle(st_x2 - dot_r, bot_y2, dot_r, stroke=1, fill=1)

    # Thép sườn khi H >= 700
    if cs.get("is_deep"):
        mid_y = (st_y1 + st_y2) / 2.0
        c.circle(st_x1 + dot_r, mid_y, dot_r, stroke=1, fill=1)
        c.circle(st_x2 - dot_r, mid_y, dot_r, stroke=1, fill=1)

    # 4. Leader ghi chú thép góc 135°
    c.setLineWidth(LW_DIM_PT)
    c.setFont(FONT_REGULAR, 5.5)

    # Leader Thép trên
    elbow_tx = sec_right_x + 8.0
    elbow_ty = sec_top_y + 4.0
    c.line(sec_right_x - cover - dot_r, st_y2 - dot_r, elbow_tx, elbow_ty)
    c.line(elbow_tx, elbow_ty, elbow_tx + 22.0, elbow_ty)
    lbl_top = cs["top_main"]["label"]
    if cs.get("top_extra"):
        lbl_top += f"+{cs['top_extra']['label']}"
    c.drawString(elbow_tx + 1.0, elbow_ty + 1.5, lbl_top)

    # Leader Thép dưới
    elbow_bx = sec_right_x + 8.0
    elbow_by = sec_bot_y - 4.0
    c.line(sec_right_x - cover - dot_r, st_y1 + dot_r, elbow_bx, elbow_by)
    c.line(elbow_bx, elbow_by, elbow_bx + 22.0, elbow_by)
    lbl_bot = cs["bot_main"]["label"]
    if cs.get("bot_extra"):
        lbl_bot += f"+{cs['bot_extra']['label']}"
    c.drawString(elbow_bx + 1.0, elbow_by + 1.5, lbl_bot)

    # Leader Cốt đai bên trái
    elbow_sx = sec_left_x - 7.0
    elbow_sy = (sec_bot_y + sec_top_y) / 2.0 + 3.0
    c.line(sec_left_x + cover, (sec_bot_y + sec_top_y) / 2.0, elbow_sx, elbow_sy)
    c.line(elbow_sx, elbow_sy, elbow_sx - 20.0, elbow_sy)
    c.drawRightString(elbow_sx - 1.0, elbow_sy + 1.5, cs.get("stirrup", "d6a100"))

    # 5. Kích thước b và h
    draw_pdf_dim_line(c, sec_left_x, sec_bot_y - 8.0, sec_right_x, sec_bot_y - 8.0, f"{b_width}")
    # Dim h bên trái
    c.line(sec_left_x - 8.0, sec_bot_y, sec_left_x - 8.0, sec_top_y)
    c.line(sec_left_x - 10.0, sec_bot_y - 2, sec_left_x - 6.0, sec_bot_y + 2)
    c.line(sec_left_x - 10.0, sec_top_y - 2, sec_left_x - 6.0, sec_top_y + 2)
    c.drawRightString(sec_left_x - 10.0, (sec_bot_y + sec_top_y) / 2.0 - 2, f"{b_depth}")

    # 6. Tiêu đề mặt cắt bên dưới
    c.setFont(FONT_BOLD, 7.0)
    c.drawCentredString(sec_center_x, sec_bot_y - 18.0, cs["title"])
    c.setFont(FONT_REGULAR, 5.5)
    c.setFillColorRGB(*COLOR_GRAY)
    sub_title = f"{cs.get('sub', '')} ({b_width}x{b_depth})"
    c.drawCentredString(sec_center_x, sec_bot_y - 24.5, sub_title)

    c.restoreState()


# ==============================================================================
# AUTOCAD DXF GENERATION (CHUẨN 1:1 MM VỚI ĐẦY ĐỦ MẶT CẮT & TITLE Ở ĐÁY)
# ==============================================================================

def generate_beam_dxf(beam_groups, combine_short=True, layout_settings=None, page_scope='all', page_range=None, current_page_index=1):
    """
    Tạo file DXF (AutoCAD R2010) với các layer chuyên nghiệp:
    - BE_TONG: Trắng/Đen (Color 7, Lineweight 35)
    - THEP_CHU / THEP_TANG_CUONG: Đỏ/Magenta (Color 1/6, Lineweight 50)
    - COT_DAI: Cyan (Color 4, Lineweight 15)
    - DIM: Xanh lá (Color 3, Lineweight 9)
    - TRUC: Đỏ linetype CENTER (Color 1, Lineweight 15)
    - TEXT / KHUNG_TEN: Trắng (Color 7, Lineweight 15 / 50)
    - Đầy đủ toàn bộ hệ thống mặt cắt 1-1, 2-2, 3-3... ở nửa dưới bản vẽ.
    - Tiêu đề bản vẽ đặt ở đáy khung (Align Bottom).
    """
    doc = get_template_dxf_doc()
    msp = doc.modelspace()

    ensure_layer(doc, "BE_TONG", color=7, lineweight=35)
    ensure_layer(doc, "THEP_CHU", color=1, lineweight=50)
    ensure_layer(doc, "THEP_TANG_CUONG", color=6, lineweight=50)
    ensure_layer(doc, "COT_DAI", color=4, lineweight=15)
    ensure_layer(doc, "DIM", color=3, lineweight=9)
    ensure_layer(doc, "TRUC", color=1, linetype="CENTER", lineweight=15)
    ensure_layer(doc, "TEXT", color=7, lineweight=15)
    ensure_layer(doc, "KHUNG_TEN", color=7, lineweight=50)

    all_pages = build_pages_list(beam_groups, combine_short=combine_short)
    if not all_pages:
        stream = io.StringIO()
        doc.write(stream)
        return stream.getvalue().encode('utf-8')

    total_doc_pages = len(all_pages)

    if page_scope == 'current':
        idx = max(1, min(int(current_page_index or 1), total_doc_pages))
        selected_indices = [idx]
    elif page_scope == 'range' and page_range:
        if isinstance(page_range, str):
            selected_indices = parse_page_range(page_range, total_doc_pages)
        else:
            selected_indices = [i for i in page_range if 1 <= i <= total_doc_pages]
        if not selected_indices:
            selected_indices = list(range(1, total_doc_pages + 1))
    else:
        selected_indices = list(range(1, total_doc_pages + 1))

    ctx_data = get_etabs_context()

    y_offset = 0.0
    gap_y = 5000.0 # Khoảng cách giữa các bản vẽ trong Modelspace (5000mm)

    for orig_page_num in selected_indices:
        page_info = all_pages[orig_page_num - 1]
        beams = page_info["beams"]
        if page_info["type"] == "combined" and len(beams) >= 2:
            draw_combined_dxf_sheet(msp, beams[0], beams[1], 0, y_offset, ctx_data=ctx_data)
        else:
            draw_single_dxf_sheet(msp, beams[0], 0, y_offset, ctx_data=ctx_data)
        y_offset += (14850.0 + gap_y)

    stream = io.StringIO()
    doc.write(stream)
    return stream.getvalue().encode('utf-8')


def draw_single_dxf_sheet(msp, bg, base_x, base_y, ctx_data=None):
    """Vẽ 1 bản vẽ dầm hoàn chỉnh trên ModelSpace AutoCAD (đơn vị thực tế mm)."""
    scale = 50 # Tỷ lệ 1/50
    sheet_w = 420.0 * scale # 21000 mm
    sheet_h = 297.0 * scale # 14850 mm

    # Khung bản vẽ A3 ngoài
    msp.add_lwpolyline([(base_x, base_y), (base_x + sheet_w, base_y), (base_x + sheet_w, base_y + sheet_h), (base_x, base_y + sheet_h), (base_x, base_y)], dxfattribs={"layer": "KHUNG_TEN"})
    # Khung viền trong
    msp.add_lwpolyline([(base_x + 500, base_y + 500), (base_x + sheet_w - 500, base_y + 500), (base_x + sheet_w - 500, base_y + sheet_h - 500), (base_x + 500, base_y + sheet_h - 500), (base_x + 500, base_y + 500)], dxfattribs={"layer": "KHUNG_TEN"})

    draw_beam_entities_dxf(msp, bg, base_x + 1000, base_y + 1000, sheet_w - 2000, sheet_h - 2000, ctx_data=ctx_data)


def draw_combined_dxf_sheet(msp, bg1, bg2, base_x, base_y, ctx_data=None):
    """Vẽ 2 dầm ngắn kết hợp trên cùng 1 khung A3 (AutoCAD)."""
    scale = 50
    sheet_w = 420.0 * scale # 21000 mm
    sheet_h = 297.0 * scale # 14850 mm

    # Khung A3
    msp.add_lwpolyline([(base_x, base_y), (base_x + sheet_w, base_y), (base_x + sheet_w, base_y + sheet_h), (base_x, base_y + sheet_h), (base_x, base_y)], dxfattribs={"layer": "KHUNG_TEN"})
    msp.add_lwpolyline([(base_x + 500, base_y + 500), (base_x + sheet_w - 500, base_y + 500), (base_x + sheet_w - 500, base_y + sheet_h - 500), (base_x + 500, base_y + sheet_h - 500), (base_x + 500, base_y + 500)], dxfattribs={"layer": "KHUNG_TEN"})

    # Đường phân cách nét đứt ở giữa
    mid_y = base_y + sheet_h / 2.0
    msp.add_line((base_x + 600, mid_y), (base_x + sheet_w - 600, mid_y), dxfattribs={"layer": "KHUNG_TEN", "linetype": "DASHED"})

    half_h = (sheet_h - 2000) / 2.0
    # Dầm 1 ở nửa trên
    draw_beam_entities_dxf(msp, bg1, base_x + 1000, mid_y + 500, sheet_w - 2000, half_h, title_prefix="[NỬA TRÊN] ", ctx_data=ctx_data)
    # Dầm 2 ở nửa dưới
    draw_beam_entities_dxf(msp, bg2, base_x + 1000, base_y + 1000, sheet_w - 2000, half_h, title_prefix="[NỬA DƯỚI] ", ctx_data=ctx_data)


def draw_beam_entities_dxf(msp, bg, bx, by, bw, bh, title_prefix="", ctx_data=None):
    """Vẽ dầm dọc, cốt thép 0.50mm, toàn bộ mặt cắt và Tiêu đề dầm ở đáy (Align Bottom) trên DXF."""
    spans = bg.get("beams", [])
    if not spans:
        return

    long_id = bg.get("long_beam_id", spans[0].get("label", "BEAM"))
    story = bg.get("story", spans[0].get("story", "T1"))
    sec = bg.get("commonSection", spans[0].get("section", "200x400"))
    b_depth = spans[0].get("depth", 400)
    b_width = spans[0].get("width", 200)

    # Xác định phương X hay Y
    is_x = True
    if spans and spans[0].get("direction"):
        is_x = (spans[0].get("direction") == 'X')
    elif spans and spans[0].get("p1") and spans[0].get("p2"):
        dx = abs(spans[0]["p2"][0] - spans[0]["p1"][0])
        dy = abs(spans[0]["p2"][1] - spans[0]["p1"][1])
        is_x = (dx >= dy)

    columns = ctx_data.get("columns", []) if ctx_data else []
    grids = ctx_data.get("grids", {}) if ctx_data else {}

    num_spans = len(spans)
    has_col = [check_column_at_support(spans, i, is_x, columns) for i in range(num_spans + 1)]
    support_coords = []
    for i in range(num_spans):
        b = spans[i]
        p1 = b.get("p1", [0, 0])
        p2 = b.get("p2", [0, 0])
        support_coords.append(min(p1[0 if is_x else 1], p2[0 if is_x else 1]))
    last_b = spans[-1]
    last_p1 = last_b.get("p1", [0, 0])
    last_p2 = last_b.get("p2", [0, 0])
    support_coords.append(max(last_p1[0 if is_x else 1], last_p2[0 if is_x else 1]))
    grid_labels = [get_grid_bubble_label(coord, is_x, grids) for coord in support_coords]

    # 1. TIÊU ĐỀ BẢN VẼ: ĐƯA XUỐNG ALIGN BOTTOM
    story_str = format_story_name(story)
    axis_name = bg.get("axisName") or spans[0].get("axisName") or ""
    axis_part = f" • TRỤC {axis_name.replace('Trục ', '').strip().upper()}" if axis_name else ""
    clean_sec = re.sub(r'^[bB]\s*', '', sec).strip()
    title_text = f"{title_prefix}BẢN VẼ CHI TIẾT DẦM: {long_id} • {story_str}{axis_part} ({num_spans} NHỊP • {clean_sec})"
    msp.add_text(title_text, dxfattribs={"layer": "TEXT", "height": 320}).set_placement((bx + bw / 2.0, by + 200), align=TextEntityAlignment.BOTTOM_CENTER)

    # 2. PHÂN BỔ TỌA ĐỘ ELEVATION Ở NỬA TRÊN
    elev_base_y = by + bh * 0.48
    cur_x = bx + 500
    total_len = sum(b.get("length", 4000) for b in spans)
    span_coords = []

    for b in spans:
        l = b.get("length", 4000)
        h = b.get("depth", b_depth)
        # Bê tông dầm
        msp.add_lwpolyline([(cur_x, elev_base_y), (cur_x + l, elev_base_y), (cur_x + l, elev_base_y + h), (cur_x, elev_base_y + h), (cur_x, elev_base_y)], dxfattribs={"layer": "BE_TONG"})
        span_coords.append({"x1": cur_x, "x2": cur_x + l, "len": l, "h": h, "beam": b})
        cur_x += l

    start_x = span_coords[0]["x1"]
    end_x = span_coords[-1]["x2"]

    # Cột đỡ tại các gối
    col_w = 400
    col_h = 500
    for i, sc in enumerate(span_coords):
        if has_col[i]:
            msp.add_lwpolyline([(sc["x1"] - col_w/2, elev_base_y - col_h), (sc["x1"] + col_w/2, elev_base_y - col_h), (sc["x1"] + col_w/2, elev_base_y), (sc["x1"] - col_w/2, elev_base_y), (sc["x1"] - col_w/2, elev_base_y - col_h)], dxfattribs={"layer": "BE_TONG"})
        if i == len(span_coords) - 1 and has_col[i + 1]:
            msp.add_lwpolyline([(sc["x2"] - col_w/2, elev_base_y - col_h), (sc["x2"] + col_w/2, elev_base_y - col_h), (sc["x2"] + col_w/2, elev_base_y), (sc["x2"] - col_w/2, elev_base_y), (sc["x2"] - col_w/2, elev_base_y - col_h)], dxfattribs={"layer": "BE_TONG"})

    # 3. THÉP CHỦ TRÊN VÀ DƯỚI (THEP_CHU: Nét 50)
    top_y = elev_base_y + b_depth - 35
    bot_y = elev_base_y + 35
    msp.add_line((start_x + 35, top_y), (end_x - 35, top_y), dxfattribs={"layer": "THEP_CHU"})
    # Móc neo bẻ 90° chúc xuống và vát vào
    hook_depth = b_depth - 70
    msp.add_line((start_x + 35, top_y), (start_x + 35, top_y - hook_depth), dxfattribs={"layer": "THEP_CHU"})
    msp.add_line((start_x + 35, top_y - hook_depth), (start_x + 85, top_y - hook_depth + 50), dxfattribs={"layer": "THEP_CHU"})
    msp.add_line((end_x - 35, top_y), (end_x - 35, top_y - hook_depth), dxfattribs={"layer": "THEP_CHU"})
    msp.add_line((end_x - 35, top_y - hook_depth), (end_x - 85, top_y - hook_depth + 50), dxfattribs={"layer": "THEP_CHU"})

    msp.add_line((start_x + 35, bot_y), (end_x - 35, bot_y), dxfattribs={"layer": "THEP_CHU"})
    msp.add_line((start_x + 35, bot_y), (start_x + 35, bot_y + 150), dxfattribs={"layer": "THEP_CHU"})
    msp.add_line((start_x + 35, bot_y + 150), (start_x + 85, bot_y + 150 - 50), dxfattribs={"layer": "THEP_CHU"})
    msp.add_line((end_x - 35, bot_y), (end_x - 35, bot_y + 150), dxfattribs={"layer": "THEP_CHU"})
    msp.add_line((end_x - 35, bot_y + 150), (end_x - 85, bot_y + 150 - 50), dxfattribs={"layer": "THEP_CHU"})

    # 4. THÉP TĂNG CƯỜNG GỐI TRÊN & BỤNG DƯỚI (THEP_TANG_CUONG: Nét 50)
    top_extra_y = top_y - 50
    for i, sc in enumerate(span_coords):
        q = sc["len"] * 0.25
        if i == 0:
            msp.add_line((sc["x1"] + 35, top_extra_y), (sc["x1"] + q, top_extra_y), dxfattribs={"layer": "THEP_TANG_CUONG"})
        if i < len(span_coords) - 1:
            next_q = span_coords[i+1]["len"] * 0.25
            msp.add_line((sc["x2"] - q, top_extra_y), (sc["x2"] + next_q, top_extra_y), dxfattribs={"layer": "THEP_TANG_CUONG"})
        else:
            msp.add_line((sc["x2"] - q, top_extra_y), (sc["x2"] - 35, top_extra_y), dxfattribs={"layer": "THEP_TANG_CUONG"})

    for sc in span_coords:
        if sc["len"] >= 2000:
            cut_l = sc["len"] * 0.15
            cut_r = sc["len"] * 0.85
            bot_extra_y = bot_y + 50
            msp.add_line((sc["x1"] + cut_l, bot_extra_y), (sc["x1"] + cut_r, bot_extra_y), dxfattribs={"layer": "THEP_TANG_CUONG"})

    # 5. KÍCH THƯỚC (DIM: Nét 9)
    dim_y = elev_base_y - 600
    for sc in span_coords:
        msp.add_line((sc["x1"], dim_y), (sc["x2"], dim_y), dxfattribs={"layer": "DIM"})
        msp.add_line((sc["x1"], dim_y - 100), (sc["x1"], elev_base_y), dxfattribs={"layer": "DIM"})
        msp.add_line((sc["x2"], dim_y - 100), (sc["x2"], elev_base_y), dxfattribs={"layer": "DIM"})
        msp.add_text(f"{int(sc['len'])}", dxfattribs={"layer": "DIM", "height": 180}).set_placement(((sc["x1"] + sc["x2"]) / 2.0, dim_y + 40), align=TextEntityAlignment.BOTTOM_CENTER)

    dim_tot_y = dim_y - 500
    msp.add_line((start_x, dim_tot_y), (end_x, dim_tot_y), dxfattribs={"layer": "DIM"})
    msp.add_line((start_x, dim_tot_y - 100), (start_x, elev_base_y), dxfattribs={"layer": "DIM"})
    msp.add_line((end_x, dim_tot_y - 100), (end_x, elev_base_y), dxfattribs={"layer": "DIM"})
    msp.add_text(f"{int(total_len)}", dxfattribs={"layer": "DIM", "height": 220}).set_placement(((start_x + end_x) / 2.0, dim_tot_y + 40), align=TextEntityAlignment.BOTTOM_CENTER)

    # 6. KÝ HIỆU TRỤC TRÒN VÀ TIM TRỤC
    grid_y = dim_tot_y - 600
    for i in range(num_spans + 1):
        if not has_col[i]:
            continue
        x_col = span_coords[i]["x1"] if i < num_spans else span_coords[-1]["x2"]
        lbl = grid_labels[i] or f"{i+1}"
        msp.add_circle((x_col, grid_y), 250, dxfattribs={"layer": "TRUC"})
        msp.add_text(lbl, dxfattribs={"layer": "TRUC", "height": 180}).set_placement((x_col, grid_y - 90), align=TextEntityAlignment.MIDDLE_CENTER)
        msp.add_line((x_col, grid_y + 250), (x_col, elev_base_y + b_depth + 600), dxfattribs={"layer": "TRUC", "linetype": "CENTER"})

    # 7. VẼ TOÀN BỘ CÁC MẶT CẮT (CROSS SECTIONS) NỬA DƯỚI TRÊN DXF
    cs_base_y = by + 1200
    all_sections = []
    cut_counter = 1
    for s_idx, sc in enumerate(span_coords):
        b = sc["beam"]
        w = b.get("width", 200)
        h = b.get("depth", 400)
        reb_main_top = parse_rebar_spec(b.get("rebar_main_top") or bg.get("rebar_main_top", "2D18"))
        reb_main_bot = parse_rebar_spec(b.get("rebar_main_bot") or bg.get("rebar_main_bot", "2D18"))
        reb_top_l = parse_rebar_spec(b.get("extra_top_left") or b.get("rebar_top_left"))
        reb_bot_m = parse_rebar_spec(b.get("extra_bot_mid") or b.get("rebar_bot_mid"))
        reb_top_r = parse_rebar_spec(b.get("extra_top_right") or b.get("rebar_top_right"))

        if sc["len"] < 2000:
            idx = cut_counter
            cut_counter += 1
            all_sections.append({"title": f"{idx}-{idx}", "w": w, "h": h, "top": reb_main_top, "top_ext": reb_top_l if reb_top_l["count"] > 0 else None, "bot": reb_main_bot, "bot_ext": None})
        else:
            idx1, idx2, idx3 = cut_counter, cut_counter + 1, cut_counter + 2
            cut_counter += 3
            all_sections.append({"title": f"{idx1}-{idx1}", "w": w, "h": h, "top": reb_main_top, "top_ext": reb_top_l if reb_top_l["count"] > 0 else None, "bot": reb_main_bot, "bot_ext": None})
            all_sections.append({"title": f"{idx2}-{idx2}", "w": w, "h": h, "top": reb_main_top, "top_ext": None, "bot": reb_main_bot, "bot_ext": reb_bot_m if reb_bot_m["count"] > 0 else None})
            all_sections.append({"title": f"{idx3}-{idx3}", "w": w, "h": h, "top": reb_main_top, "top_ext": reb_top_r if reb_top_r["count"] > 0 else None, "bot": reb_main_bot, "bot_ext": None})

    cols_per_row = min(6, len(all_sections)) if all_sections else 1
    slot_w = (bw - 1000) / max(1, cols_per_row)
    for idx, cs in enumerate(all_sections):
        row = idx // cols_per_row
        col = idx % cols_per_row
        cs_cx = bx + 500 + col * slot_w + slot_w / 2.0
        cs_cy = cs_base_y + (1 - row) * 2200

        # Thân mặt cắt bê tông
        sw = cs["w"] * 2.0
        sh = cs["h"] * 2.0
        msp.add_lwpolyline([(cs_cx - sw/2, cs_cy), (cs_cx + sw/2, cs_cy), (cs_cx + sw/2, cs_cy + sh), (cs_cx - sw/2, cs_cy + sh), (cs_cx - sw/2, cs_cy)], dxfattribs={"layer": "BE_TONG"})
        # Đai
        msp.add_lwpolyline([(cs_cx - sw/2 + 30, cs_cy + 30), (cs_cx + sw/2 - 30, cs_cy + 30), (cs_cx + sw/2 - 30, cs_cy + sh - 30), (cs_cx - sw/2 + 30, cs_cy + sh - 30), (cs_cx - sw/2 + 30, cs_cy + 30)], dxfattribs={"layer": "COT_DAI"})
        # Thép chủ trên tròn
        msp.add_circle((cs_cx - sw/2 + 50, cs_cy + sh - 50), 16, dxfattribs={"layer": "THEP_CHU"})
        msp.add_circle((cs_cx + sw/2 - 50, cs_cy + sh - 50), 16, dxfattribs={"layer": "THEP_CHU"})
        # Thép chủ dưới tròn
        msp.add_circle((cs_cx - sw/2 + 50, cs_cy + 50), 16, dxfattribs={"layer": "THEP_CHU"})
        msp.add_circle((cs_cx + sw/2 - 50, cs_cy + 50), 16, dxfattribs={"layer": "THEP_CHU"})

        # Leader và text thép trên
        lbl_top = cs["top"]["label"]
        if cs.get("top_ext"):
            lbl_top += f"+{cs['top_ext']['label']}"
        msp.add_line((cs_cx + sw/2 - 50, cs_cy + sh - 50), (cs_cx + sw/2 + 120, cs_cy + sh + 80), dxfattribs={"layer": "TEXT"})
        msp.add_line((cs_cx + sw/2 + 120, cs_cy + sh + 80), (cs_cx + sw/2 + 450, cs_cy + sh + 80), dxfattribs={"layer": "TEXT"})
        msp.add_text(lbl_top, dxfattribs={"layer": "TEXT", "height": 110}).set_placement((cs_cx + sw/2 + 130, cs_cy + sh + 95))

        # Leader và text thép dưới
        lbl_bot = cs["bot"]["label"]
        if cs.get("bot_ext"):
            lbl_bot += f"+{cs['bot_ext']['label']}"
        msp.add_line((cs_cx + sw/2 - 50, cs_cy + 50), (cs_cx + sw/2 + 120, cs_cy - 80), dxfattribs={"layer": "TEXT"})
        msp.add_line((cs_cx + sw/2 + 120, cs_cy - 80), (cs_cx + sw/2 + 450, cs_cy - 80), dxfattribs={"layer": "TEXT"})
        msp.add_text(lbl_bot, dxfattribs={"layer": "TEXT", "height": 110}).set_placement((cs_cx + sw/2 + 130, cs_cy - 70))

        # Kích thước mặt cắt b và h
        msp.add_line((cs_cx - sw/2, cs_cy - 80), (cs_cx + sw/2, cs_cy - 80), dxfattribs={"layer": "DIM"})
        msp.add_text(f"{cs['w']}", dxfattribs={"layer": "DIM", "height": 100}).set_placement((cs_cx, cs_cy - 70), align=TextEntityAlignment.BOTTOM_CENTER)
        msp.add_line((cs_cx - sw/2 - 80, cs_cy), (cs_cx - sw/2 - 80, cs_cy + sh), dxfattribs={"layer": "DIM"})
        msp.add_text(f"{cs['h']}", dxfattribs={"layer": "DIM", "height": 100}).set_placement((cs_cx - sw/2 - 95, cs_cy + sh/2), align=TextEntityAlignment.MIDDLE_RIGHT)

        # Tiêu đề mặt cắt bên dưới
        msp.add_text(f"MẶT CẮT {cs['title']}", dxfattribs={"layer": "TEXT", "height": 160}).set_placement((cs_cx, cs_cy - 250), align=TextEntityAlignment.BOTTOM_CENTER)
        msp.add_text(f"{cs['w']}x{cs['h']}", dxfattribs={"layer": "TEXT", "height": 130}).set_placement((cs_cx, cs_cy - 420), align=TextEntityAlignment.BOTTOM_CENTER)
