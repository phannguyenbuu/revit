#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
column_cad_exporter.py
Bộ xuất bản vẽ kỹ thuật chi tiết Tiết diện Cột toàn nhà (Bảng Grid 18 Cột × 4 Tầng).
Định dạng xuất: PDF (vector chuẩn TCVN) và DXF (AutoCAD R2010).

Quy chuẩn phong cách (Style) đúng 100% theo section_cross dầm:
- Thép chủ: Đậm nét 0.50 mm (Màu đỏ / Layer THEP_CHU)
- Nét dim kích thước: Mảnh 0.09 mm (Màu xanh lá / Layer DIM)
- Nét bê tông, cốt đai, trục, leader, ghi chú: 0.15 mm (Layer BE_TONG, COT_DAI, TEXT)
- Khung bảng, khung tên bản vẽ: 0.35 mm (Layer KHUNG_TEN)
- Cốt đai viền trong lùi 25mm bê tông bảo vệ, kèm 2 móc xéo 135 độ ở góc
- Dimension b và h kèm vạch gạch chéo 45 độ chuẩn CAD
- Leader chỉ thép góc 135 độ kèm giá nằm ngang đặt text phía trên
"""

import os
import io
import math
import json
import re
from reportlab.lib.pagesizes import A1, A2, A3, landscape
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
        print(f"[Exporter] Khong the dang ky font Arial: {e}")

FONT_REGULAR = "Arial" if HAS_ARIAL else "Helvetica"
FONT_BOLD = "Arial-Bold" if HAS_ARIAL else "Helvetica-Bold"

# Hằng số quy đổi mm sang pt trong ReportLab (72 pt / inch, 1 inch = 25.4 mm)
MM_TO_PT = 72.0 / 25.4

# Chiều dày nét in PDF chuẩn
LW_REBAR_PT = 0.50 * MM_TO_PT   # 0.50 mm = 1.417 pt
LW_DIM_PT = 0.09 * MM_TO_PT     # 0.09 mm = 0.255 pt
LW_DEFAULT_PT = 0.15 * MM_TO_PT # 0.15 mm = 0.425 pt
LW_BORDER_PT = 0.35 * MM_TO_PT  # 0.35 mm

# Kích thước khổ giấy A1 ngang (841 x 594 mm) cho bảng 18 cột x 4 tầng rộng rãi, rõ nét
SHEET_W_MM = 841.0
SHEET_H_MM = 594.0
SHEET_W_PT = SHEET_W_MM * MM_TO_PT # 2383.94 pt
SHEET_H_PT = SHEET_H_MM * MM_TO_PT # 1683.78 pt

# Cấu hình cốt thép mặc định cho các tiết diện cột trong dự án
COLUMN_SECTION_DEFAULTS = {
    "C1 250x300": {
        "width": 250, "depth": 300,
        "rebar_str": "4Φ18", "corner_count": 4, "side_count_x": 0, "side_count_y": 0,
        "stirrup_str": "d6a100/200", "has_crosstie": False
    },
    "C2 300x300": {
        "width": 300, "depth": 300,
        "rebar_str": "4Φ20", "corner_count": 4, "side_count_x": 0, "side_count_y": 0,
        "stirrup_str": "d6a100/200", "has_crosstie": False
    },
    "C3 250x520": {
        "width": 250, "depth": 520,
        "rebar_str": "8Φ20", "corner_count": 4, "side_count_x": 0, "side_count_y": 2,
        "stirrup_str": "d6a100/200", "has_crosstie": True
    },
    "C4 200x300": {
        "width": 200, "depth": 300,
        "rebar_str": "4Φ18", "corner_count": 4, "side_count_x": 0, "side_count_y": 0,
        "stirrup_str": "d6a100/200", "has_crosstie": False
    },
    "C5 250x250": {
        "width": 250, "depth": 250,
        "rebar_str": "4Φ18", "corner_count": 4, "side_count_x": 0, "side_count_y": 0,
        "stirrup_str": "d6a100/200", "has_crosstie": False
    }
}

STORY_LEVELS = [
    {"id": "T4", "name": "TẦNG 4", "elevation": "+10.800", "height": 3.6},
    {"id": "T3", "name": "TẦNG 3", "elevation": "+7.200", "height": 3.6},
    {"id": "T2", "name": "TẦNG 2", "elevation": "+3.600", "height": 3.6},
    {"id": "T1", "name": "TẦNG 1", "elevation": "±0.000", "height": 3.6}
]


class MatrixCells(dict):
    """Dictionary lưu trữ cells hỗ trợ cả key chuỗi 'T1_C1' (cho JSON) và tuple ('T1', 'C1') (cho Python)."""
    def get(self, key, default=None):
        if isinstance(key, tuple):
            return super().get(f"{key[0]}_{key[1]}", default)
        return super().get(key, default)

    def __getitem__(self, key):
        if isinstance(key, tuple):
            return super().__getitem__(f"{key[0]}_{key[1]}")
        return super().__getitem__(key)

    def __contains__(self, key):
        if isinstance(key, tuple):
            return super().__contains__(f"{key[0]}_{key[1]}")
        return super().__contains__(key)


def get_column_matrix_data(etabs_data=None):
    """
    Trích xuất và tổ chức ma trận dữ liệu 18 cột (C1..C18) × 4 tầng (T4, T3, T2, T1).
    """
    if etabs_data is None:
        try:
            import etabs_service
            etabs_data = etabs_service.get_etabs_data()
        except Exception:
            try:
                with open("etabs_beam_data.json", "r", encoding="utf-8") as f:
                    etabs_data = json.load(f)
            except Exception:
                etabs_data = {}

    grids_x = etabs_data.get("grids", {}).get("X", [])
    grids_y = etabs_data.get("grids", {}).get("Y", [])
    raw_columns = etabs_data.get("columns", [])

    def find_nearest_grid(val, grid_list):
        if not grid_list:
            return "?"
        best = min(grid_list, key=lambda g: abs(g.get("ordinate", 0) - val))
        return best.get("id", "?")

    # Bản đồ vị trí lưới trục và tọa độ của từng mã cột
    column_meta = {}
    for c in raw_columns:
        lbl = c.get("label")
        if lbl and lbl not in column_meta:
            x, y = c.get("p1", [0, 0, 0])[:2]
            gx = find_nearest_grid(x, grids_x)
            gy = find_nearest_grid(y, grids_y)
            column_meta[lbl] = {
                "label": lbl,
                "grid": f"{gx}-{gy}",
                "grid_x": gx,
                "grid_y": gy,
                "coord": [round(x), round(y)]
            }

    # Gom nhóm theo story và label
    col_by_story_label = {}
    for c in raw_columns:
        st = c.get("story")
        lbl = c.get("label")
        if st and lbl:
            col_by_story_label[(st, lbl)] = c

    column_labels = [f"C{i}" for i in range(1, 16)]
    stories = STORY_LEVELS

    # Xây dựng bảng ma trận cells
    grid_cells = MatrixCells()
    for st_info in stories:
        st_id = st_info["id"]
        for lbl in column_labels:
            col_obj = col_by_story_label.get((st_id, lbl))
            k_id = f"{st_id}_{lbl}"
            if col_obj:
                sec_name = col_obj.get("section", "C1 250x300")
                sec_cfg = COLUMN_SECTION_DEFAULTS.get(sec_name)
                
                # Phân tích kích thước nếu không có trong preset
                b_w = col_obj.get("width")
                b_h = col_obj.get("depth")
                if not b_w or not b_h:
                    m = re.search(r'(\d+)\s*[xX]\s*(\d+)', sec_name)
                    if m:
                        b_w, b_h = float(m.group(1)), float(m.group(2))
                    else:
                        b_w, b_h = 250.0, 300.0

                if not sec_cfg:
                    # Tự động suy diễn cốt thép cho tiết diện mới
                    if b_h >= 500:
                        sec_cfg = {
                            "width": b_w, "depth": b_h,
                            "rebar_str": "8Φ20", "corner_count": 4, "side_count_x": 0, "side_count_y": 2,
                            "stirrup_str": "d6a100/200", "has_crosstie": True
                        }
                    else:
                        sec_cfg = {
                            "width": b_w, "depth": b_h,
                            "rebar_str": "4Φ18", "corner_count": 4, "side_count_x": 0, "side_count_y": 0,
                            "stirrup_str": "d6a100/200", "has_crosstie": False
                        }

                meta = column_meta.get(lbl, {"grid": "---", "coord": [0, 0]})

                grid_cells[k_id] = {
                    "exists": True,
                    "story": st_id,
                    "label": lbl,
                    "section_name": sec_name,
                    "width": b_w,
                    "depth": b_h,
                    "rebar_str": sec_cfg["rebar_str"],
                    "corner_count": sec_cfg["corner_count"],
                    "side_count_x": sec_cfg["side_count_x"],
                    "side_count_y": sec_cfg["side_count_y"],
                    "stirrup_str": sec_cfg["stirrup_str"],
                    "has_crosstie": sec_cfg["has_crosstie"],
                    "grid": meta.get("grid", "---"),
                    "coord": meta.get("coord", [0, 0])
                }
            else:
                meta = column_meta.get(lbl, {"grid": "---", "coord": [0, 0]})
                grid_cells[k_id] = {
                    "exists": False,
                    "story": st_id,
                    "label": lbl,
                    "grid": meta.get("grid", "---"),
                    "coord": meta.get("coord", [0, 0])
                }

    return {
        "model_name": etabs_data.get("model_name", "CAI_TAO_PHUONG_AN_B.EDB"),
        "column_labels": column_labels,
        "stories": stories,
        "column_meta": column_meta,
        "cells": grid_cells
    }


# ==============================================================================
# HÀM VẼ DIMENSION CAD TRÊN REPORTLAB PDF
# ==============================================================================

def draw_pdf_cad_dim(c, x1, y1, x2, y2, text, offset=12, is_vertical=False):
    """Vẽ đường gióng kích thước chuẩn CAD với vạch tick 45 độ và text canh giữa."""
    c.saveState()
    c.setLineWidth(LW_DIM_PT)
    c.setStrokeColorRGB(0.12, 0.45, 0.2) # Xanh lá đậm chuẩn CAD
    c.setFillColorRGB(0.12, 0.45, 0.2)
    c.setFont(FONT_BOLD, 5.0)

    tick_len = 2.2
    if not is_vertical:
        dy = y1 + offset
        # Đường gióng chân
        c.line(x1, y1 + (2 if offset > 0 else -2), x1, dy + (2 if offset > 0 else -2))
        c.line(x2, y2 + (2 if offset > 0 else -2), x2, dy + (2 if offset > 0 else -2))
        # Đường kích thước chính
        c.line(x1, dy, x2, dy)
        # Vạch chéo 45 độ
        c.line(x1 - tick_len, dy - tick_len, x1 + tick_len, dy + tick_len)
        c.line(x2 - tick_len, dy - tick_len, x2 + tick_len, dy + tick_len)
        # Con số đo
        c.drawCentredString((x1 + x2) / 2.0, dy + (2.5 if offset > 0 else -6.5), str(text))
    else:
        dx = x1 + offset
        # Đường gióng chân
        c.line(x1 + (2 if offset > 0 else -2), y1, dx + (2 if offset > 0 else -2), y1)
        c.line(x2 + (2 if offset > 0 else -2), y2, dx + (2 if offset > 0 else -2), y2)
        # Đường kích thước chính
        c.line(dx, y1, dx, y2)
        # Vạch chéo 45 độ
        c.line(dx - tick_len, y1 - tick_len, dx + tick_len, y1 + tick_len)
        c.line(dx - tick_len, y2 - tick_len, dx + tick_len, y2 + tick_len)
        # Con số đo (xoay 90 độ)
        c.saveState()
        c.translate(dx + (-4.0 if offset < 0 else 6.5), (y1 + y2) / 2.0)
        c.rotate(90)
        c.drawCentredString(0, 0, str(text))
        c.restoreState()
    c.restoreState()


# ==============================================================================
# HÀM VẼ CELL MẶT CẮT TIẾT DIỆN CỘT TRÊN REPORTLAB PDF
# ==============================================================================

def draw_column_cross_section_pdf(c, cell_data, cell_x, cell_y, cell_w, cell_h):
    """
    Vẽ 1 mặt cắt cột trong 1 cell theo đúng 100% phong cách section_cross dầm:
    - Bê tông chữ nhật
    - Cốt đai bo góc lùi 25mm + móc neo 135 độ
    - Cốt đai móc C (nếu 8 cây thép)
    - Chấm thép tròn ĐẬM NÉT 0.50 mm màu đỏ
    - Dim kích thước b và h mảnh 0.09 mm màu xanh lá
    - Leader chỉ thép góc 135 độ kèm shelf ngang đặt text
    - Leader chỉ đai
    - Tiêu đề tiết diện phía dưới
    """
    if not cell_data or not cell_data.get("exists"):
        # Ô trống (không có cột)
        c.saveState()
        c.setStrokeColorRGB(0.85, 0.88, 0.92)
        c.setLineWidth(0.5)
        # Vẽ 2 đường chéo mờ
        c.setDash(3, 3)
        c.line(cell_x + 6, cell_y + 6, cell_x + cell_w - 6, cell_y + cell_h - 6)
        c.line(cell_x + 6, cell_y + cell_h - 6, cell_x + cell_w - 6, cell_y + 6)
        c.setDash()
        c.setFont(FONT_REGULAR, 6.0)
        c.setFillColorRGB(0.6, 0.65, 0.72)
        c.drawCentredString(cell_x + cell_w / 2.0, cell_y + cell_h / 2.0 - 2, "— KHÔNG CÓ CỘT —")
        c.restoreState()
        return

    b_w = cell_data.get("width", 250.0)
    b_h = cell_data.get("depth", 300.0)
    sec_name = cell_data.get("section_name", "250x300")
    rebar_str = cell_data.get("rebar_str", "4Φ18")
    stirrup_str = cell_data.get("stirrup_str", "d6a100/200")
    has_crosstie = cell_data.get("has_crosstie", False)

    # Tỉ lệ vẽ mặt cắt: Scale mm -> pt để vừa vặn trong cell
    # Cell rộng cell_w, cao cell_h. Dành 65% diện tích ở giữa cho mặt cắt
    max_draw_w = cell_w * 0.44
    max_draw_h = cell_h * 0.48
    
    scale_x = max_draw_w / max(1.0, b_w)
    scale_y = max_draw_h / max(1.0, b_h)
    scale = min(scale_x, scale_y) # Đồng tỉ lệ isometric không méo

    draw_w = b_w * scale
    draw_h = b_h * scale

    # Tâm vẽ hình
    cx = cell_x + cell_w / 2.0
    cy = cell_y + cell_h * 0.52

    rect_x = cx - draw_w / 2.0
    rect_y = cy - draw_h / 2.0

    # 1. BÊ TÔNG MẶT CẮT (Nét 0.15 mm, stroke xám đậm, fill trắng)
    c.saveState()
    c.setLineWidth(LW_DEFAULT_PT)
    c.setStrokeColorRGB(0.2, 0.25, 0.35)
    c.setFillColorRGB(1.0, 1.0, 1.0)
    c.rect(rect_x, rect_y, draw_w, draw_h, fill=1, stroke=1)
    c.restoreState()

    # 2. CỐT ĐAI (Nét 0.15 mm, Màu Cyan #0284c7)
    # Lớp bê tông bảo vệ c = 25mm quy đổi theo scale
    cover_pt = max(2.2, 25.0 * scale)
    st_x = rect_x + cover_pt
    st_y = rect_y + cover_pt
    st_w = max(4.0, draw_w - cover_pt * 2.0)
    st_h = max(4.0, draw_h - cover_pt * 2.0)

    c.saveState()
    c.setLineWidth(LW_DEFAULT_PT)
    c.setStrokeColorRGB(0.0, 0.52, 0.78)
    c.rect(st_x, st_y, st_w, st_h, stroke=1)

    # 2 móc bẻ xéo 135 độ ở góc trên bên trái
    hook_len = max(2.5, 30.0 * scale)
    c.line(st_x + 1.2, st_y + st_h - 1.2, st_x + 1.2 + hook_len * 0.7, st_y + st_h - 1.2 - hook_len * 0.7)
    c.line(st_x + 2.5, st_y + st_h - 1.2, st_x + 2.5 + hook_len * 0.7, st_y + st_h - 1.2 - hook_len * 0.7)

    # Nếu có đai móc C hoặc đai lồng liên kết cạnh dài (khi có 8 thanh thép)
    if has_crosstie and st_h > 20:
        c.setStrokeColorRGB(0.0, 0.6, 0.85)
        # Đai liên kết ngang ở các vị trí chia 3
        y_tie1 = st_y + st_h / 3.0
        y_tie2 = st_y + 2.0 * st_h / 3.0
        c.line(st_x, y_tie1, st_x + st_w, y_tie1)
        c.line(st_x, y_tie2, st_x + st_w, y_tie2)
        # Móc đai C ở 2 đầu
        c.line(st_x, y_tie1, st_x + 2.5, y_tie1 + 2.0)
        c.line(st_x + st_w, y_tie1, st_x + st_w - 2.5, y_tie1 + 2.0)
        c.line(st_x, y_tie2, st_x + 2.5, y_tie2 + 2.0)
        c.line(st_x + st_w, y_tie2, st_x + st_w - 2.5, y_tie2 + 2.0)
    c.restoreState()

    # 3. CỐT THÉP DỌC (Chấm tròn đặc ĐẬM NÉT 0.50 MM - Màu Đỏ Nổi Bật)
    r_pt = max(1.8, min(2.8, 10.0 * scale))
    rebar_coords = []

    # 4 thanh góc (luôn có)
    corner_inset = max(r_pt + 1.0, cover_pt + r_pt * 0.6)
    x_left = rect_x + corner_inset
    x_right = rect_x + draw_w - corner_inset
    y_bot = rect_y + corner_inset
    y_top = rect_y + draw_h - corner_inset

    rebar_coords.append((x_left, y_top))
    rebar_coords.append((x_right, y_top))
    rebar_coords.append((x_left, y_bot))
    rebar_coords.append((x_right, y_bot))

    # Thanh thép sườn (chỉ khi có 8 cây, ví dụ C3 250x520 hoặc b_h >= 500)
    is_8_bars = has_crosstie or rebar_str.startswith("8") or cell_data.get("side_count_y", 0) > 0 or b_h >= 500
    if is_8_bars:
        y_mid1 = y_bot + (y_top - y_bot) / 3.0
        y_mid2 = y_bot + 2.0 * (y_top - y_bot) / 3.0
        rebar_coords.append((x_left, y_mid1))
        rebar_coords.append((x_right, y_mid1))
        rebar_coords.append((x_left, y_mid2))
        rebar_coords.append((x_right, y_mid2))

    c.saveState()
    c.setFillColorRGB(0.86, 0.12, 0.12) # Đỏ chuẩn TCVN
    c.setStrokeColorRGB(0.45, 0.05, 0.05)
    c.setLineWidth(0.4)
    for (rx, ry) in rebar_coords:
        c.circle(rx, ry, r_pt, fill=1, stroke=1)
    c.restoreState()

    # 4. DIM KÍCH THƯỚC (Nét 0.09 mm, Màu Xanh Lá)
    # Dim ngang bên dưới: b
    dim_off_b = -max(7.0, draw_h * 0.18)
    draw_pdf_cad_dim(c, rect_x, rect_y, rect_x + draw_w, rect_y, f"{int(b_w)}", offset=dim_off_b, is_vertical=False)

    # Dim dọc bên trái: h
    dim_off_h = -max(7.0, draw_w * 0.22)
    draw_pdf_cad_dim(c, rect_x, rect_y, rect_x, rect_y + draw_h, f"{int(b_h)}", offset=dim_off_h, is_vertical=True)

    # 5. LEADER CHỈ CỐT THÉP DỌC (Góc 135 độ sang phải, shelf ngang, text phía trên)
    c.saveState()
    c.setLineWidth(LW_DEFAULT_PT)
    c.setStrokeColorRGB(0.85, 0.12, 0.12)
    c.setFillColorRGB(0.85, 0.12, 0.12)
    c.setFont(FONT_BOLD, 5.5)

    lead_target_x = x_right
    lead_target_y = y_top
    lead_slant_dx = max(6.0, draw_w * 0.22)
    lead_slant_dy = max(5.0, draw_h * 0.18)
    lead_elbow_x = lead_target_x + lead_slant_dx
    lead_elbow_y = lead_target_y + lead_slant_dy
    lead_shelf_len = max(24.0, c.stringWidth(rebar_str, FONT_BOLD, 5.5) + 4)
    lead_end_x = min(cell_x + cell_w - 2, lead_elbow_x + lead_shelf_len)

    c.line(lead_target_x, lead_target_y, lead_elbow_x, lead_elbow_y)
    c.line(lead_elbow_x, lead_elbow_y, lead_end_x, lead_elbow_y)
    c.drawString(lead_elbow_x + 2, lead_elbow_y + 2, rebar_str)
    c.restoreState()

    # 6. LEADER CHỈ CỐT ĐAI (Góc 135 độ sang trái, shelf ngang, text phía trên)
    c.saveState()
    c.setLineWidth(LW_DEFAULT_PT)
    c.setStrokeColorRGB(0.0, 0.52, 0.78)
    c.setFillColorRGB(0.0, 0.52, 0.78)
    c.setFont(FONT_BOLD, 4.8)

    st_target_x = st_x
    st_target_y = cy
    st_slant_dx = -max(5.0, draw_w * 0.18)
    st_slant_dy = max(5.0, draw_h * 0.16)
    st_elbow_x = st_target_x + st_slant_dx
    st_elbow_y = st_target_y + st_slant_dy
    st_text_w = c.stringWidth(stirrup_str, FONT_BOLD, 4.8)
    st_shelf_len = max(20.0, st_text_w + 4)
    st_end_x = max(cell_x + 2, st_elbow_x - st_shelf_len)

    # Chấm tròn nhỏ tại điểm chỉ đai
    c.circle(st_target_x, st_target_y, 1.0, fill=1)
    c.line(st_target_x, st_target_y, st_elbow_x, st_elbow_y)
    c.line(st_elbow_x, st_elbow_y, st_end_x, st_elbow_y)
    c.drawString(st_end_x + 1, st_elbow_y + 2, stirrup_str)
    c.restoreState()

    # 7. TIÊU ĐỀ TIẾT DIỆN PHÍA DƯỚI (Mã cột & Kích thước b x h)
    c.saveState()
    c.setFont(FONT_BOLD, 6.0)
    c.setFillColorRGB(0.1, 0.15, 0.25)
    title_y = cell_y + 6
    clean_sec = sec_name.replace("C1 ", "").replace("C2 ", "").replace("C3 ", "").replace("C4 ", "").replace("C5 ", "")
    c.drawCentredString(cx, title_y, f"{cell_data['label']} ({clean_sec})")
    c.restoreState()


# ==============================================================================
# BỘ XUẤT BẢN VẼ PDF CHO CỘT (REPORTLAB VECTOR)
# ==============================================================================

def generate_column_pdf(column_matrix=None, output_path=None):
    """
    Tạo bản vẽ PDF chi tiết tiết diện cột (Grid 18 cột × 4 tầng)
    Khổ A1 ngang, khung tên chuẩn, đầy đủ chi tiết tiết diện và ghi chú kỹ thuật.
    """
    if isinstance(column_matrix, str):
        output_path = column_matrix
        column_matrix = None

    if column_matrix is None:
        column_matrix = get_column_matrix_data()

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(SHEET_W_PT, SHEET_H_PT))

    # Kích thước lề trang in A1
    margin_left = 25.0 * MM_TO_PT   # 25 mm lề gáy đóng tập
    margin_right = 10.0 * MM_TO_PT  # 10 mm
    margin_top = 10.0 * MM_TO_PT    # 10 mm
    margin_bottom = 10.0 * MM_TO_PT # 10 mm

    drawable_w = SHEET_W_PT - margin_left - margin_right
    drawable_h = SHEET_H_PT - margin_top - margin_bottom

    # 1. KHUNG BẢN VẼ VÀ KHUNG TÊN (Nét 0.35 mm)
    c.saveState()
    c.setLineWidth(LW_BORDER_PT)
    c.setStrokeColorRGB(0.1, 0.1, 0.15)
    c.rect(margin_left, margin_bottom, drawable_w, drawable_h)

    # Viền ngoài đôi chuẩn CAD
    c.setLineWidth(0.6)
    c.rect(margin_left - 3, margin_bottom - 3, drawable_w + 6, drawable_h + 6)
    c.restoreState()

    # 2. KHUNG TIÊU ĐỀ TRÊN ĐẦU BẢN VẼ
    header_h_pt = 36.0 * MM_TO_PT
    title_box_y = SHEET_H_PT - margin_top - header_h_pt

    c.saveState()
    c.setFillColorRGB(0.08, 0.12, 0.22)
    c.setFont(FONT_BOLD, 14.0)
    c.drawString(margin_left + 15, title_box_y + header_h_pt - 18, "BẢNG CHI TIẾT TIẾT DIỆN CỘT QUA CÁC TẦNG (GRID 15 CỘT × 4 TẦNG)")
    
    c.setFont(FONT_REGULAR, 8.5)
    c.setFillColorRGB(0.3, 0.35, 0.45)
    model_name = column_matrix.get("model_name", "CAI_TAO_PHUONG_AN_B.EDB")
    c.drawString(margin_left + 15, title_box_y + header_h_pt - 32, f"DỰ ÁN: {model_name}  •  QUY CHUẨN: TCVN 5574:2018  •  TỈ LỆ TIẾT DIỆN: 1/25  •  BÊ TÔNG B22.5 (M300)  •  THÉP DỌC CB400-V, ĐAI CB240-T")

    # Đường kẻ ngang phân cách header
    c.setLineWidth(LW_BORDER_PT)
    c.setStrokeColorRGB(0.1, 0.1, 0.15)
    c.line(margin_left, title_box_y, margin_left + drawable_w, title_box_y)
    c.restoreState()

    # 3. GHI CHÚ KỸ THUẬT GÓC DƯỚI (Không cần khung tên theo yêu cầu người dùng)
    notes_x = margin_left + 15
    notes_y = margin_bottom + 6
    c.saveState()
    c.setFont(FONT_BOLD, 7.0)
    c.setFillColorRGB(0.15, 0.2, 0.3)
    c.drawString(notes_x, notes_y + 10, "GHI CHÚ THI CÔNG:")
    c.setFont(FONT_REGULAR, 6.5)
    c.setFillColorRGB(0.3, 0.35, 0.45)
    c.drawString(notes_x + 85, notes_y + 10, "1. Lớp bê tông bảo vệ c = 25mm. Chiều dài đoạn nối chồng L_nối >= 35d (>= 700mm).  |  2. Cốt đai d6a100 bố trí dày ở 2 đầu cột (500mm tính từ mặt dầm/sàn), vùng giữa cột bố trí a200. Thép CB400-V, đai CB240-T.")
    c.restoreState()

    # 4. TÍNH TOÁN KÍCH THƯỚC BẢNG GRID 15 CỘT × 4 TẦNG (Tối ưu hóa chiều cao tối đa)
    grid_area_x = margin_left
    grid_area_y = margin_bottom + 24
    grid_area_w = drawable_w
    grid_area_h = title_box_y - grid_area_y - 6

    # Cột đầu tiên dành cho Tiêu đề Tầng (Stories header column)
    story_col_w = 48.0 * MM_TO_PT
    cols_area_w = grid_area_w - story_col_w

    column_labels = column_matrix.get("column_labels", [f"C{i}" for i in range(1, 16)])
    cell_w = cols_area_w / float(len(column_labels))

    # Chiều cao hàng tiêu đề cột (Column Labels & Grid axes)
    col_header_h = 24.0 * MM_TO_PT
    rows_area_h = grid_area_h - col_header_h
    cell_h = rows_area_h / 4.0

    stories = column_matrix.get("stories", STORY_LEVELS)
    cells = column_matrix.get("cells", {})
    col_meta = column_matrix.get("column_meta", {})

    # 6. VẼ VIỀN VÀ NỀN BẢNG MA TRẬN
    c.saveState()
    c.setLineWidth(LW_BORDER_PT)
    c.setStrokeColorRGB(0.2, 0.25, 0.35)
    c.rect(grid_area_x, grid_area_y, grid_area_w, grid_area_h)

    # Nền cho hàng tiêu đề cột
    c.setFillColorRGB(0.94, 0.96, 0.98)
    c.rect(grid_area_x, grid_area_y + rows_area_h, grid_area_w, col_header_h, fill=1, stroke=1)

    # Nền cho cột tiêu đề tầng
    c.setFillColorRGB(0.96, 0.97, 0.99)
    c.rect(grid_area_x, grid_area_y, story_col_w, rows_area_h, fill=1, stroke=1)

    # Ô góc giao nhau (Header Stories x Header Columns)
    c.setFillColorRGB(0.91, 0.93, 0.96)
    c.rect(grid_area_x, grid_area_y + rows_area_h, story_col_w, col_header_h, fill=1, stroke=1)
    # Đường chéo ô góc
    c.setLineWidth(0.4)
    c.line(grid_area_x, grid_area_y + grid_area_h, grid_area_x + story_col_w, grid_area_y + rows_area_h)
    c.setFont(FONT_BOLD, 7.5)
    c.setFillColorRGB(0.15, 0.2, 0.3)
    c.drawString(grid_area_x + story_col_w * 0.46, grid_area_y + rows_area_h + col_header_h * 0.62, "MÃ CỘT")
    c.drawString(grid_area_x + 8, grid_area_y + rows_area_h + col_header_h * 0.22, "TẦNG")
    c.restoreState()

    # 7. VẼ TIÊU ĐỀ 18 CỘT (MÃ CỘT & LƯỚI TRỤC)
    c.saveState()
    c.setLineWidth(0.4)
    c.setStrokeColorRGB(0.65, 0.7, 0.78)
    for col_idx, lbl in enumerate(column_labels):
        col_x = grid_area_x + story_col_w + col_idx * cell_w
        # Đường kẻ dọc phân cách các cột
        c.line(col_x, grid_area_y, col_x, grid_area_y + grid_area_h)

        meta = col_meta.get(lbl, {"grid": "---"})
        grid_axis_str = meta.get("grid", "---")
        if grid_axis_str != "---":
            grid_axis_str = f"Trục {grid_axis_str}"

        # Mã Cột (Ví dụ C1, C2...)
        c.setFont(FONT_BOLD, 9.5)
        c.setFillColorRGB(0.08, 0.15, 0.3)
        c.drawCentredString(col_x + cell_w / 2.0, grid_area_y + rows_area_h + col_header_h * 0.58, lbl)

        # Lưới trục (Ví dụ Trục 1-C)
        c.setFont(FONT_REGULAR, 6.5)
        c.setFillColorRGB(0.35, 0.42, 0.52)
        c.drawCentredString(col_x + cell_w / 2.0, grid_area_y + rows_area_h + col_header_h * 0.20, grid_axis_str)
    c.restoreState()

    # 8. VẼ TIÊU ĐỀ 4 TẦNG VÀ CÁC CELL TIẾT DIỆN CỘT
    # Hàng 0 ở trên cùng: T4, Hàng 1: T3, Hàng 2: T2, Hàng 3: T1
    c.saveState()
    for row_idx, st_info in enumerate(stories):
        st_id = st_info["id"]
        # y tính từ dưới lên: row_idx = 0 (T4) nằm trên cùng -> y lớn nhất
        cell_y = grid_area_y + (3 - row_idx) * cell_h

        # Đường kẻ ngang phân cách hàng
        c.setLineWidth(0.5)
        c.setStrokeColorRGB(0.65, 0.7, 0.78)
        c.line(grid_area_x, cell_y, grid_area_x + grid_area_w, cell_y)

        # Tiêu đề tầng ở cột đầu tiên
        c.setFont(FONT_BOLD, 8.5)
        c.setFillColorRGB(0.12, 0.2, 0.35)
        c.drawCentredString(grid_area_x + story_col_w / 2.0, cell_y + cell_h * 0.58, st_info["name"])

        c.setFont(FONT_REGULAR, 7.0)
        c.setFillColorRGB(0.35, 0.45, 0.55)
        c.drawCentredString(grid_area_x + story_col_w / 2.0, cell_y + cell_h * 0.38, f"Cốt: {st_info['elevation']}")

        # Vẽ các cell của từng cột trên tầng này
        for col_idx, lbl in enumerate(column_labels):
            cell_x = grid_area_x + story_col_w + col_idx * cell_w
            cell_data = cells.get((st_id, lbl))
            
            # Khung clip và vẽ cross section
            c.saveState()
            draw_column_cross_section_pdf(c, cell_data, cell_x, cell_y, cell_w, cell_h)
            c.restoreState()

    c.restoreState()

    c.showPage()
    c.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()

    if output_path:
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

    return pdf_bytes


# ==============================================================================
# BỘ XUẤT BẢN VẼ DXF CHO CỘT (AUTOCAD R2010 VỚI LAYER & LINEWEIGHTS CHUẨN)
# ==============================================================================

def generate_column_dxf(column_matrix=None, output_path=None):
    """
    Tạo file DXF (AutoCAD R2010) cho Bảng Tiết diện Cột 18 cột × 4 tầng:
    - Layer BE_TONG: Trắng/Đen (Color 7), Nét 15 (0.15 mm)
    - Layer THEP_CHU: Đỏ (Color 1), Nét 50 (0.50 mm)
    - Layer COT_DAI: Cyan (Color 4), Nét 15 (0.15 mm)
    - Layer DIM: Xanh lá (Color 3), Nét 9 (0.09 mm)
    - Layer TRUC: Đỏ Center (Color 1), Nét 15 (0.15 mm)
    - Layer TEXT: Trắng (Color 7), Nét 15 (0.15 mm)
    - Layer KHUNG_TEN: Trắng (Color 7), Nét 35 (0.35 mm)
    - Layer KHUNG_GRID: Xám (Color 8), Nét 25 (0.25 mm)
    """
    if isinstance(column_matrix, str):
        output_path = column_matrix
        column_matrix = None

    if column_matrix is None:
        column_matrix = get_column_matrix_data()

    doc = get_template_dxf_doc()
    msp = doc.modelspace()

    # 1. TẠO CÁC LAYER CHUẨN KỸ THUẬT
    ensure_layer(doc, "BE_TONG", color=7, lineweight=15)
    ensure_layer(doc, "THEP_CHU", color=1, lineweight=50)
    ensure_layer(doc, "COT_DAI", color=4, lineweight=15)
    ensure_layer(doc, "DIM", color=3, lineweight=9)
    ensure_layer(doc, "TRUC", color=1, linetype="CENTER", lineweight=15)
    ensure_layer(doc, "TEXT", color=7, lineweight=15)
    ensure_layer(doc, "KHUNG_TEN", color=7, lineweight=35)
    ensure_layer(doc, "KHUNG_GRID", color=8, lineweight=25)

    column_labels = column_matrix.get("column_labels", [f"C{i}" for i in range(1, 16)])
    stories = column_matrix.get("stories", STORY_LEVELS)
    cells = column_matrix.get("cells", {})
    col_meta = column_matrix.get("column_meta", {})

    # Trong không gian AutoCAD (đơn vị mm thực tế):
    # Mỗi cell có kích thước thực: 1200mm rộng × 1500mm cao
    cell_w_cad = 1200.0
    cell_h_cad = 1500.0
    story_col_w_cad = 1600.0
    header_h_cad = 700.0

    total_w = story_col_w_cad + len(column_labels) * cell_w_cad
    total_h = header_h_cad + 4 * cell_h_cad

    base_x = 0.0
    base_y = 0.0

    # 2. KHUNG NGOÀI BẢNG MA TRẬN
    msp.add_lwpolyline(
        [(base_x, base_y), (base_x + total_w, base_y),
         (base_x + total_w, base_y + total_h), (base_x, base_y + total_h),
         (base_x, base_y)],
        dxfattribs={"layer": "KHUNG_GRID"}
    )

    # Đường phân chia cột Tiêu đề tầng
    msp.add_line((base_x + story_col_w_cad, base_y), (base_x + story_col_w_cad, base_y + total_h), dxfattribs={"layer": "KHUNG_GRID"})
    # Đường phân chia hàng Tiêu đề cột
    grid_top_y = base_y + 4 * cell_h_cad
    msp.add_line((base_x, grid_top_y), (base_x + total_w, grid_top_y), dxfattribs={"layer": "KHUNG_GRID"})

    # Đường chéo ô góc
    msp.add_line((base_x, base_y + total_h), (base_x + story_col_w_cad, grid_top_y), dxfattribs={"layer": "KHUNG_GRID"})
    msp.add_text("MA COT", dxfattribs={"layer": "TEXT", "height": 70}).set_placement((base_x + story_col_w_cad * 0.55, grid_top_y + header_h_cad * 0.6))
    msp.add_text("TANG", dxfattribs={"layer": "TEXT", "height": 70}).set_placement((base_x + 100, grid_top_y + header_h_cad * 0.25))

    # 3. KẺ ĐƯỜNG DỌC PHÂN CÁCH 18 CỘT VÀ GHI NHÃN
    for col_idx, lbl in enumerate(column_labels):
        cx = base_x + story_col_w_cad + col_idx * cell_w_cad
        if col_idx > 0:
            msp.add_line((cx, base_y), (cx, base_y + total_h), dxfattribs={"layer": "KHUNG_GRID"})

        meta = col_meta.get(lbl, {"grid": "---"})
        grid_axis_str = meta.get("grid", "---")
        if grid_axis_str != "---":
            grid_axis_str = f"TRUC {grid_axis_str}"

        # Text Mã Cột
        t_lbl = msp.add_text(lbl, dxfattribs={"layer": "TEXT", "height": 90})
        t_lbl.set_placement((cx + cell_w_cad / 2.0, grid_top_y + header_h_cad * 0.55), align=TextEntityAlignment.MIDDLE_CENTER)

        # Text Trục
        t_axis = msp.add_text(grid_axis_str, dxfattribs={"layer": "TEXT", "height": 65})
        t_axis.set_placement((cx + cell_w_cad / 2.0, grid_top_y + header_h_cad * 0.25), align=TextEntityAlignment.MIDDLE_CENTER)

    # 4. KẺ ĐƯỜNG NGANG PHÂN CÁCH 4 TẦNG VÀ VẼ TIẾT DIỆN TỪNG Ô
    for row_idx, st_info in enumerate(stories):
        st_id = st_info["id"]
        cy_bot = base_y + (3 - row_idx) * cell_h_cad
        cy_top = cy_bot + cell_h_cad

        if row_idx < 3:
            msp.add_line((base_x, cy_bot), (base_x + total_w, cy_bot), dxfattribs={"layer": "KHUNG_GRID"})

        # Text Tiêu đề tầng
        t_st = msp.add_text(st_info["name"], dxfattribs={"layer": "TEXT", "height": 90})
        t_st.set_placement((base_x + story_col_w_cad / 2.0, cy_bot + cell_h_cad * 0.6), align=TextEntityAlignment.MIDDLE_CENTER)

        t_elev = msp.add_text(f"COT {st_info['elevation']}", dxfattribs={"layer": "TEXT", "height": 65})
        t_elev.set_placement((base_x + story_col_w_cad / 2.0, cy_bot + cell_h_cad * 0.38), align=TextEntityAlignment.MIDDLE_CENTER)

        # Vẽ từng cell
        for col_idx, lbl in enumerate(column_labels):
            cell_x = base_x + story_col_w_cad + col_idx * cell_w_cad
            cell_data = cells.get((st_id, lbl))

            if not cell_data or not cell_data.get("exists"):
                # Ô trống
                msp.add_line((cell_x + 100, cy_bot + 100), (cell_x + cell_w_cad - 100, cy_top - 100), dxfattribs={"layer": "KHUNG_GRID", "linetype": "DASHED"})
                msp.add_line((cell_x + 100, cy_top - 100), (cell_x + cell_w_cad - 100, cy_bot + 100), dxfattribs={"layer": "KHUNG_GRID", "linetype": "DASHED"})
                t_none = msp.add_text("- KHONG CO COT -", dxfattribs={"layer": "TEXT", "height": 55})
                t_none.set_placement((cell_x + cell_w_cad / 2.0, cy_bot + cell_h_cad / 2.0), align=TextEntityAlignment.MIDDLE_CENTER)
                continue

            # Vẽ mặt cắt thực tế (tỉ lệ 1:1 trong cell CAD)
            b_w = cell_data.get("width", 250.0)
            b_h = cell_data.get("depth", 300.0)
            rebar_str = cell_data.get("rebar_str", "4Φ18")
            stirrup_str = cell_data.get("stirrup_str", "d6a100/200")
            has_crosstie = cell_data.get("has_crosstie", False)

            mid_x = cell_x + cell_w_cad / 2.0
            mid_y = cy_bot + cell_h_cad * 0.52

            rx1 = mid_x - b_w / 2.0
            rx2 = mid_x + b_w / 2.0
            ry1 = mid_y - b_h / 2.0
            ry2 = mid_y + b_h / 2.0

            # Bê tông cột (Layer BE_TONG)
            msp.add_lwpolyline([(rx1, ry1), (rx2, ry1), (rx2, ry2), (rx1, ry2), (rx1, ry1)], dxfattribs={"layer": "BE_TONG"})

            # Cốt đai viền trong lùi 25mm (Layer COT_DAI)
            c_cov = 25.0
            st_x1, st_x2 = rx1 + c_cov, rx2 - c_cov
            st_y1, st_y2 = ry1 + c_cov, ry2 - c_cov
            msp.add_lwpolyline([(st_x1, st_y1), (st_x2, st_y1), (st_x2, st_y2), (st_x1, st_y2), (st_x1, st_y1)], dxfattribs={"layer": "COT_DAI"})

            # 2 Móc bẻ 135 độ ở góc
            msp.add_line((st_x1, st_y2), (st_x1 + 35, st_y2 - 35), dxfattribs={"layer": "COT_DAI"})
            msp.add_line((st_x1 + 10, st_y2), (st_x1 + 45, st_y2 - 35), dxfattribs={"layer": "COT_DAI"})

            # Đai liên kết ngang (nếu 8 cây)
            if has_crosstie and (st_y2 - st_y1) > 200:
                y_c1 = st_y1 + (st_y2 - st_y1) / 3.0
                y_c2 = st_y1 + 2.0 * (st_y2 - st_y1) / 3.0
                msp.add_line((st_x1, y_c1), (st_x2, y_c1), dxfattribs={"layer": "COT_DAI"})
                msp.add_line((st_x1, y_c2), (st_x2, y_c2), dxfattribs={"layer": "COT_DAI"})

            # Chấm thép tròn đặc (Layer THEP_CHU)
            r_dot = 10.0
            rebar_pts = [
                (st_x1 + r_dot, st_y2 - r_dot),
                (st_x2 - r_dot, st_y2 - r_dot),
                (st_x1 + r_dot, st_y1 + r_dot),
                (st_x2 - r_dot, st_y1 + r_dot)
            ]
            is_8_bars = has_crosstie or rebar_str.startswith("8") or b_h >= 500
            if is_8_bars:
                y_m1 = st_y1 + (st_y2 - st_y1) / 3.0
                y_m2 = st_y1 + 2.0 * (st_y2 - st_y1) / 3.0
                rebar_pts.extend([
                    (st_x1 + r_dot, y_m1),
                    (st_x2 - r_dot, y_m1),
                    (st_x1 + r_dot, y_m2),
                    (st_x2 - r_dot, y_m2)
                ])

            for (px, py) in rebar_pts:
                msp.add_circle((px, py), r_dot, dxfattribs={"layer": "THEP_CHU"})
                # Hatch solid bên trong vòng tròn
                try:
                    hatch = msp.add_hatch(color=1, dxfattribs={"layer": "THEP_CHU"})
                    hatch.paths.add_polyline_path([(px-r_dot, py), (px, py+r_dot), (px+r_dot, py), (px, py-r_dot)], is_closed=True)
                except Exception:
                    pass

            # Dim b bên dưới (Layer DIM)
            dim_y = ry1 - 120
            msp.add_line((rx1, ry1 - 20), (rx1, dim_y - 20), dxfattribs={"layer": "DIM"})
            msp.add_line((rx2, ry1 - 20), (rx2, dim_y - 20), dxfattribs={"layer": "DIM"})
            msp.add_line((rx1, dim_y), (rx2, dim_y), dxfattribs={"layer": "DIM"})
            msp.add_line((rx1 - 15, dim_y - 15), (rx1 + 15, dim_y + 15), dxfattribs={"layer": "DIM"})
            msp.add_line((rx2 - 15, dim_y - 15), (rx2 + 15, dim_y + 15), dxfattribs={"layer": "DIM"})
            t_dim_b = msp.add_text(f"{int(b_w)}", dxfattribs={"layer": "DIM", "height": 55})
            t_dim_b.set_placement(((rx1 + rx2) / 2.0, dim_y + 25), align=TextEntityAlignment.MIDDLE_CENTER)

            # Dim h bên trái (Layer DIM)
            dim_x = rx1 - 120
            msp.add_line((rx1 - 20, ry1), (dim_x - 20, ry1), dxfattribs={"layer": "DIM"})
            msp.add_line((rx1 - 20, ry2), (dim_x - 20, ry2), dxfattribs={"layer": "DIM"})
            msp.add_line((dim_x, ry1), (dim_x, ry2), dxfattribs={"layer": "DIM"})
            msp.add_line((dim_x - 15, ry1 - 15), (dim_x + 15, ry1 + 15), dxfattribs={"layer": "DIM"})
            msp.add_line((dim_x - 15, ry2 - 15), (dim_x + 15, ry2 + 15), dxfattribs={"layer": "DIM"})
            t_dim_h = msp.add_text(f"{int(b_h)}", dxfattribs={"layer": "DIM", "height": 55, "rotation": 90})
            t_dim_h.set_placement((dim_x - 30, (ry1 + ry2) / 2.0), align=TextEntityAlignment.MIDDLE_CENTER)

            # Leader chỉ thép dọc (Layer THEP_CHU)
            lx1, ly1 = st_x2 - r_dot, st_y2 - r_dot
            lx2, ly2 = rx2 + 80, ry2 + 80
            lx3 = lx2 + 220
            msp.add_line((lx1, ly1), (lx2, ly2), dxfattribs={"layer": "THEP_CHU"})
            msp.add_line((lx2, ly2), (lx3, ly2), dxfattribs={"layer": "THEP_CHU"})
            t_reb = msp.add_text(rebar_str, dxfattribs={"layer": "THEP_CHU", "height": 60})
            t_reb.set_placement((lx2 + 10, ly2 + 15))

            # Leader chỉ cốt đai (Layer COT_DAI)
            sx1, sy1 = st_x1, mid_y
            sx2, sy2 = rx1 - 60, mid_y + 60
            sx3 = sx2 - 180
            msp.add_circle((sx1, sy1), 5.0, dxfattribs={"layer": "COT_DAI"})
            msp.add_line((sx1, sy1), (sx2, sy2), dxfattribs={"layer": "COT_DAI"})
            msp.add_line((sx2, sy2), (sx3, sy2), dxfattribs={"layer": "COT_DAI"})
            t_st = msp.add_text(stirrup_str, dxfattribs={"layer": "COT_DAI", "height": 55})
            t_st.set_placement((sx3 + 10, sy2 + 15))

            # Tiêu đề cột phía dưới (Layer TEXT)
            t_bot = msp.add_text(f"{lbl} ({int(b_w)}x{int(b_h)})", dxfattribs={"layer": "TEXT", "height": 70})
            t_bot.set_placement((mid_x, cy_bot + 120), align=TextEntityAlignment.MIDDLE_CENTER)

    # 5. TIÊU ĐỀ BẢN VẼ CHÍNH VÀ KHUNG TÊN
    title_y_dxf = base_y + total_h + 300
    msp.add_text("BANG CHI TIET TIET DIEN COT QUA CAC TANG (GRID 18 COT x 4 TANG)", dxfattribs={"layer": "TEXT", "height": 180}).set_placement((base_x + 500, title_y_dxf))
    msp.add_text(f"DU AN: {column_matrix.get('model_name', 'CAI_TAO_PHUONG_AN_B.EDB')}  -  TCVN 5574:2018  -  TI LE 1/25", dxfattribs={"layer": "TEXT", "height": 100}).set_placement((base_x + 500, title_y_dxf - 160))

    stream = io.StringIO()
    doc.write(stream)
    dxf_bytes = stream.getvalue().encode('utf-8')

    if output_path:
        with open(output_path, "wb") as f:
            f.write(dxf_bytes)

    return dxf_bytes


if __name__ == "__main__":
    print("Testing column_cad_exporter...")
    mat = get_column_matrix_data()
    print(f"Extracted matrix: {len(mat['column_labels'])} columns x {len(mat['stories'])} stories")
    
    out_pdf = "test_column_sheet.pdf"
    pdf_b = generate_column_pdf(mat, output_path=out_pdf)
    print(f"Generated PDF: {len(pdf_b)} bytes -> {out_pdf}")

    out_dxf = "test_column_sheet.dxf"
    dxf_b = generate_column_dxf(mat, output_path=out_dxf)
    print(f"Generated DXF: {len(dxf_b)} bytes -> {out_dxf}")
