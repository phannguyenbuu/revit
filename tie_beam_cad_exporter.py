#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
tie_beam_cad_exporter.py
Bộ xuất bản vẽ kỹ thuật chi tiết Đà Kiềng / Dầm Móng dọc theo Trục A, B, C (Tầng 1 / Móng).
Định dạng xuất: PDF (vector chuẩn TCVN) và DXF (AutoCAD R2010).

LƯU Ý ĐẶC BIỆT VỀ NGUYÊN LÝ KẾT CẤU:
- Đà kiềng / Dầm móng chịu PHẢN LỰC ĐẨY TỪ ĐẤT LÊN (Soil Upward Reaction q_dat > 0):
  + Chiều mô-men uốn bị ĐẢO DẤU so với dầm sàn thông thường.
  + TẠI GIỮA NHỊP: Phản lực đất đẩy lên uốn cong dầm vồng lên -> CĂNG THỚ TRÊN (LƯNG DẦM).
    => CỐT THÉP TĂNG CƯỜNG NHỊP BỐ TRÍ Ở LỚP TRÊN (LƯNG DẦM)!
  + TẠI VỊ TRÍ GỐI (CHÂN CỘT / MÓNG): Cột nén xuống chống lại phản lực đất -> CĂNG THỚ DƯỚI (BỤNG DẦM).
    => CỐT THÉP TĂNG CƯỜNG GỐI BỐ TRÍ Ở LỚP DƯỚI (BỤNG DẦM)!
  + THÉP CHỦ TRÊN & DƯỚI: Chạy suốt liên tục đối xứng nhằm chống xoắn và chống lún lệch móng.
  + Móc neo thép bẻ ke 90 độ neo chắc chắn vào đài móng / cột biên >= 35d.

Quy chuẩn nét vẽ PDF (TCVN):
- Thép chủ & thép tăng cường: Đậm nét 0.50 mm (Màu đỏ / Layer THEP_CHU)
- Nét dim kích thước: Mảnh 0.09 mm (Màu xanh lá / Layer DIM)
- Nét bê tông, đai, trục, leader, text: 0.15 mm (Layer BE_TONG, COT_DAI, TEXT)
- Khung viền và khung tên: 0.35 mm (Layer KHUNG_TEN)
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
        print(f"[TieBeamExporter] Không thể đăng ký font Arial: {e}")

FONT_REGULAR = "Arial" if HAS_ARIAL else "Helvetica"
FONT_BOLD = "Arial-Bold" if HAS_ARIAL else "Helvetica-Bold"

MM_TO_PT = 72.0 / 25.4

# Chiều dày nét in PDF chuẩn
LW_REBAR_PT = 0.50 * MM_TO_PT   # 0.50 mm = 1.417 pt
LW_DIM_PT = 0.09 * MM_TO_PT     # 0.09 mm = 0.255 pt
LW_DEFAULT_PT = 0.15 * MM_TO_PT # 0.15 mm = 0.425 pt
LW_BORDER_PT = 0.35 * MM_TO_PT  # 0.35 mm

# Khổ giấy A1 ngang (841 x 594 mm) cho toàn bộ 3 tuyến đà kiềng A, B, C
SHEET_W_MM = 841.0
SHEET_H_MM = 594.0
SHEET_W_PT = SHEET_W_MM * MM_TO_PT
SHEET_H_PT = SHEET_H_MM * MM_TO_PT


def get_tie_beam_data(json_path=None):
    """
    Trích xuất và tổ chức dữ liệu 3 tuyến đà kiềng dọc Trục A, B, C từ etabs_beam_data.json.
    Kèm thiết kế cốt thép tối ưu theo nguyên lý PHẢN LỰC ĐẤT ĐẨY LÊN.
    """
    if json_path is None:
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "etabs_beam_data.json")

    with open(json_path, "r", encoding="utf-8") as f:
        etabs_data = json.load(f)

    grids_x = {g["id"]: g["ordinate"] for g in etabs_data.get("grids", {}).get("X", [])}
    grids_y = {g["id"]: g["ordinate"] for g in etabs_data.get("grids", {}).get("Y", [])}
    columns_t1 = [c for c in etabs_data.get("columns", []) if c.get("story") == "T1"]
    beams_t1 = [b for b in etabs_data.get("beams", []) if b.get("story") == "T1"]

    # 1. Tuyến Trục C (Y = 0)
    # Gồm 4 nhịp: B2 (0->5900), B20 (5900->13250), B22 (13250->16750), B23 (16750->21850)
    axis_c_spans = [
        {
            "id": "DK-C1", "beam_label": "B2", "grid_from": "1", "grid_to": "2",
            "x1": 0.0, "x2": 5900.0, "length": 5900.0, "width": 200.0, "depth": 400.0,
            "col_from": "C1 (250x300)", "col_to": "C2 (300x300)",
            "main_top": "2Φ18", "main_bot": "2Φ18",
            "extra_top_mid": "1Φ18", "extra_bot_support": "1Φ18",
            "stirrup": "d6a100/200"
        },
        {
            "id": "DK-C2", "beam_label": "B20", "grid_from": "2", "grid_to": "3",
            "x1": 5900.0, "x2": 13250.0, "length": 7350.0, "width": 300.0, "depth": 500.0,
            "col_from": "C2 (300x300)", "col_to": "C4 (300x300)",
            "main_top": "3Φ20", "main_bot": "3Φ20",
            "extra_top_mid": "2Φ20", "extra_bot_support": "2Φ20",
            "stirrup": "d6a100/200"
        },
        {
            "id": "DK-C3", "beam_label": "B22", "grid_from": "3", "grid_to": "4*",
            "x1": 13250.0, "x2": 16750.0, "length": 3500.0, "width": 200.0, "depth": 400.0,
            "col_from": "C4 (300x300)", "col_to": "C3 (300x300)",
            "main_top": "2Φ18", "main_bot": "2Φ18",
            "extra_top_mid": "", "extra_bot_support": "1Φ18",
            "stirrup": "d6a100/200"
        },
        {
            "id": "DK-C4", "beam_label": "B23", "grid_from": "4*", "grid_to": "5",
            "x1": 16750.0, "x2": 21850.0, "length": 5100.0, "width": 200.0, "depth": 400.0,
            "col_from": "C3 (300x300)", "col_to": "C10 (300x300)",
            "main_top": "2Φ18", "main_bot": "2Φ18",
            "extra_top_mid": "1Φ18", "extra_bot_support": "1Φ18",
            "stirrup": "d6a100/200"
        }
    ]

    # 2. Tuyến Trục B (Y = 5970) - Tuyến đà kiềng chính suốt chiều dài công trình
    # Gồm 5 nhịp: B8 (0->5900), B19 (5900->13250), B21 (13250->21850), B13 (21850->27450), B12 (27450->32950)
    axis_b_spans = [
        {
            "id": "DK-B1", "beam_label": "B8", "grid_from": "1", "grid_to": "2",
            "x1": 0.0, "x2": 5900.0, "length": 5900.0, "width": 200.0, "depth": 400.0,
            "col_from": "C5 (250x300)", "col_to": "C6 (300x300)",
            "main_top": "2Φ20", "main_bot": "2Φ20",
            "extra_top_mid": "1Φ20", "extra_bot_support": "1Φ20",
            "stirrup": "d6a100/200"
        },
        {
            "id": "DK-B2", "beam_label": "B19", "grid_from": "2", "grid_to": "3",
            "x1": 5900.0, "x2": 13250.0, "length": 7350.0, "width": 300.0, "depth": 500.0,
            "col_from": "C6 (300x300)", "col_to": "C11 (250x520)",
            "main_top": "3Φ20", "main_bot": "3Φ20",
            "extra_top_mid": "2Φ20", "extra_bot_support": "2Φ20",
            "stirrup": "d6a100/200"
        },
        {
            "id": "DK-B3", "beam_label": "B21", "grid_from": "3", "grid_to": "5",
            "x1": 13250.0, "x2": 21850.0, "length": 8600.0, "width": 300.0, "depth": 500.0,
            "col_from": "C11 (250x520)", "col_to": "C12 (250x520)",
            "main_top": "3Φ20", "main_bot": "3Φ20",
            "extra_top_mid": "2Φ22", "extra_bot_support": "2Φ22",
            "stirrup": "d6a100/200"
        },
        {
            "id": "DK-B4", "beam_label": "B13", "grid_from": "5", "grid_to": "6",
            "x1": 21850.0, "x2": 27450.0, "length": 5600.0, "width": 200.0, "depth": 400.0,
            "col_from": "C12 (250x520)", "col_to": "C13 (300x300)",
            "main_top": "2Φ20", "main_bot": "2Φ20",
            "extra_top_mid": "1Φ20", "extra_bot_support": "1Φ20",
            "stirrup": "d6a100/200"
        },
        {
            "id": "DK-B5", "beam_label": "B12", "grid_from": "6", "grid_to": "7",
            "x1": 27450.0, "x2": 32950.0, "length": 5500.0, "width": 200.0, "depth": 400.0,
            "col_from": "C13 (300x300)", "col_to": "C15 (250x300)",
            "main_top": "2Φ20", "main_bot": "2Φ20",
            "extra_top_mid": "1Φ20", "extra_bot_support": "1Φ20",
            "stirrup": "d6a100/200"
        }
    ]

    # 3. Tuyến Trục A (Y = 11970)
    # Gồm 3 nhịp: B16 (18250->21850), B9 (21850->27450), B10 (27450->32950)
    axis_a_spans = [
        {
            "id": "DK-A1", "beam_label": "B16", "grid_from": "4", "grid_to": "5",
            "x1": 18250.0, "x2": 21850.0, "length": 3600.0, "width": 200.0, "depth": 400.0,
            "col_from": "C17 (250x300)", "col_to": "C18 (250x300)",
            "main_top": "2Φ18", "main_bot": "2Φ18",
            "extra_top_mid": "1Φ18", "extra_bot_support": "1Φ18",
            "stirrup": "d6a100/200"
        },
        {
            "id": "DK-A2", "beam_label": "B9", "grid_from": "5", "grid_to": "6",
            "x1": 21850.0, "x2": 27450.0, "length": 5600.0, "width": 200.0, "depth": 400.0,
            "col_from": "C18 (250x300)", "col_to": "C14 (300x300)",
            "main_top": "2Φ18", "main_bot": "2Φ18",
            "extra_top_mid": "1Φ18", "extra_bot_support": "1Φ18",
            "stirrup": "d6a100/200"
        },
        {
            "id": "DK-A3", "beam_label": "B10", "grid_from": "6", "grid_to": "7",
            "x1": 27450.0, "x2": 32950.0, "length": 5500.0, "width": 200.0, "depth": 400.0,
            "col_from": "C14 (300x300)", "col_to": "C16 (250x300)",
            "main_top": "2Φ18", "main_bot": "2Φ18",
            "extra_top_mid": "1Φ18", "extra_bot_support": "1Φ18",
            "stirrup": "d6a100/200"
        }
    ]

    return {
        "model_name": etabs_data.get("model_name", "CAI_TAO_PHUONG_AN_B.EDB"),
        "axes": [
            {
                "axis_id": "A",
                "axis_title": "ĐÀ KIỀNG TRỤC A (DK-A)",
                "elevation": "+1.800 (TẦNG 1 / MÓNG)",
                "total_len_mm": 14700.0,
                "spans": axis_a_spans,
                "support_grids": ["4", "5", "6", "7"],
                "support_cols": ["C17", "C18", "C14", "C16"],
                "y_coord": 11970.0
            },
            {
                "axis_id": "B",
                "axis_title": "ĐÀ KIỀNG TRỤC B (DK-B)",
                "elevation": "+1.800 (TẦNG 1 / MÓNG)",
                "total_len_mm": 32950.0,
                "spans": axis_b_spans,
                "support_grids": ["1", "2", "3", "5", "6", "7"],
                "support_cols": ["C5", "C6", "C11", "C12", "C13", "C15"],
                "y_coord": 5970.0
            },
            {
                "axis_id": "C",
                "axis_title": "ĐÀ KIỀNG TRỤC C (DK-C)",
                "elevation": "+1.800 (TẦNG 1 / MÓNG)",
                "total_len_mm": 21850.0,
                "spans": axis_c_spans,
                "support_grids": ["1", "2", "3", "4*", "5"],
                "support_cols": ["C1", "C2", "C4", "C3", "C10"],
                "y_coord": 0.0
            }
        ],
        "notes": [
            "NGUYÊN LÝ PHẢN LỰC ĐẨY TỪ ĐẤT LÊN (q_đất): Đà kiềng tựa trên nền đất chịu áp lực phản lực đất tác dụng từ dưới lên.",
            "Do phản lực đẩy từ dưới lên, mô-men uốn tại GIỮA NHỊP gây căng thớ TRÊN (Lưng dầm), tại VỊ TRÍ GỐI (chân cột/đài móng) gây căng thớ DƯỚI (Bụng dầm).",
            "Cốt thép tăng cường NHỊP bố trí ở LỚP TRÊN (LƯNG DẦM), chiều dài cắt thép 0.65L. Cốt thép tăng cường GỐI bố trí ở LỚP DƯỚI (BỤNG DẦM), chiều dài neo 0.25L mỗi bên.",
            "Thép chủ trên và dưới chạy suốt liên tục đối xứng nhằm chống lún lệch, chống xoắn và tăng cường độ cứng giằng móng.",
            "Bê tông đà kiềng: Cấp độ bền B22.5 (M300), Thép chủ CB400-V, Thép đai CB240-T. Lớp bê tông bảo vệ c = 35mm (có bê tông lót móng dày 100mm)."
        ]
    }


def draw_pdf_dim_line(c, x1, y1, x2, y2, text, is_bold=False):
    """Vẽ đường kích thước kèm vạch gạch chéo 45 độ chuẩn CAD."""
    c.saveState()
    c.setLineWidth(LW_DIM_PT)
    c.setStrokeColorRGB(0.1, 0.45, 0.25)
    c.line(x1, y1, x2, y2)
    # Ticks 45 độ
    tick_len = 3.0
    c.line(x1 - tick_len, y1 - tick_len, x1 + tick_len, y1 + tick_len)
    c.line(x2 - tick_len, y2 - tick_len, x2 + tick_len, y2 + tick_len)
    # Text
    c.setFont(FONT_BOLD if is_bold else FONT_REGULAR, 6.5)
    c.setFillColorRGB(0.1, 0.35, 0.2)
    c.drawCentredString((x1 + x2) / 2.0, y1 + 2.5, str(text))
    c.restoreState()


def draw_elevation_axis(c, axis_data, bx, by, bw, bh):
    """
    Vẽ hình chiếu đứng (Elevation) một tuyến đà kiềng:
    - Bê tông dầm + cổ móng/cột bên dưới
    - Mũi tên biểu diễn phản lực đất đẩy lên (q_dat)
    - Sơ đồ mô-men uốn M uốn vồng lên
    - Cốt thép: Thép tăng cường NHỊP ở LƯNG DẦM, Thép tăng cường GỐI ở BỤNG DẦM
    - Đường Dim nhịp, Dim cắt thép, Dim tổng
    - Trục tròn kiến trúc
    - Các mặt cắt ngang điển hình (Section Cross) kèm leader chỉ thép
    """
    spans = axis_data["spans"]
    total_len = axis_data["total_len_mm"]
    axis_title = axis_data["axis_title"]

    # 1. Header tuyến đà kiềng
    c.saveState()
    c.setFont(FONT_BOLD, 9.5)
    c.setFillColorRGB(0.05, 0.15, 0.35)
    c.drawString(bx + 15, by + bh - 14, f"{axis_title} • L = {total_len/1000:.2f}m • {len(spans)} NHỊP (TCVN 5574:2018 - ĐÀ KIỀNG CHỊU PHẢN LỰC ĐẤT)")
    c.restoreState()

    # Phân chia không gian: 65% cho Elevation bên trái, 35% cho các mặt cắt ngang bên phải
    elev_w = bw * 0.72
    cs_w = bw - elev_w - 20
    cs_x = bx + elev_w + 15

    margin_x = 35.0
    drawable_w = elev_w - margin_x * 2
    scale_x = drawable_w / total_len

    # Chiều cao dầm vẽ
    beam_draw_h = 24.0
    beam_top_y = by + bh * 0.58
    beam_bot_y = beam_top_y - beam_draw_h

    # A. Cổ móng / đài móng bên dưới chân cột (Nét 0.15 mm)
    col_w_pt = 18.0
    col_h_pt = 18.0
    footing_w_pt = 32.0
    footing_h_pt = 12.0

    c.saveState()
    c.setLineWidth(LW_DEFAULT_PT)
    c.setStrokeColorRGB(0.3, 0.35, 0.45)
    c.setFillColorRGB(0.92, 0.94, 0.97)

    cur_x = bx + margin_x
    span_coords = []
    support_xs = [cur_x]

    for sp in spans:
        span_w = sp["length"] * scale_x
        # Khung bê tông dầm
        c.rect(cur_x, beam_bot_y, span_w, beam_draw_h, fill=1, stroke=1)
        span_coords.append({
            "span": sp, "x1": cur_x, "x2": cur_x + span_w, "w": span_w,
            "len": sp["length"], "depth": sp["depth"], "width": sp["width"]
        })
        cur_x += span_w
        support_xs.append(cur_x)

    # Vẽ cổ cột và đài móng tại các gối
    for sx in support_xs:
        # Cổ cột
        c.rect(sx - col_w_pt / 2.0, beam_bot_y - col_h_pt, col_w_pt, col_h_pt, fill=1, stroke=1)
        # Đài móng tượng trưng
        c.rect(sx - footing_w_pt / 2.0, beam_bot_y - col_h_pt - footing_h_pt, footing_w_pt, footing_h_pt, fill=1, stroke=1)
    c.restoreState()

    # B. MŨI TÊN BIỂU DIỄN PHẢN LỰC ĐẤT ĐẨY TỪ DƯỚI LÊN (q_đất)
    # Mũi tên màu cam/nâu hổ phách hướng từ dưới lên đáy dầm
    c.saveState()
    c.setLineWidth(0.8)
    c.setStrokeColorRGB(0.85, 0.45, 0.05)
    c.setFillColorRGB(0.85, 0.45, 0.05)
    for sc in span_coords:
        # Mỗi nhịp vẽ 4-5 mũi tên đẩy lên
        arrow_count = max(3, int(sc["w"] / 30.0))
        dx_arrow = sc["w"] / (arrow_count + 1)
        for ai in range(1, arrow_count + 1):
            ax = sc["x1"] + ai * dx_arrow
            ay_bot = beam_bot_y - 14
            ay_top = beam_bot_y - 2
            c.line(ax, ay_bot, ax, ay_top)
            # Đầu mũi tên hướng LÊN
            p = c.beginPath()
            p.moveTo(ax, ay_top)
            p.lineTo(ax - 2.5, ay_top - 4)
            p.lineTo(ax + 2.5, ay_top - 4)
            p.close()
            c.drawPath(p, fill=1, stroke=0)

    # Chữ "Phản lực đất q_đất ↑"
    c.setFont(FONT_BOLD, 6.5)
    c.drawString(span_coords[0]["x1"] + 10, beam_bot_y - 22, "▲▲▲ PHẢN LỰC ĐẤT NỀN ĐẨY LÊN (q_đất > 0) ▲▲▲")
    c.restoreState()

    # C. CỐT ĐAI (Nét 0.15 mm - Màu Cyan)
    c.saveState()
    c.setLineWidth(LW_DEFAULT_PT)
    c.setStrokeColorRGB(0.05, 0.55, 0.75)
    for sc in span_coords:
        st_x1 = sc["x1"] + 3
        st_x2 = sc["x2"] - 3
        q_len = sc["w"] * 0.25
        step_dense = max(2.8, q_len / 7.0)
        cx = st_x1
        # Gối trái dày a100
        while cx <= st_x1 + q_len:
            c.line(cx, beam_bot_y + 2, cx, beam_top_y - 2)
            cx += step_dense
        # Nhịp thưa a200
        step_mid = step_dense * 2.0
        while cx <= st_x2 - q_len:
            c.line(cx, beam_bot_y + 2, cx, beam_top_y - 2)
            cx += step_mid
        # Gối phải dày a100
        while cx <= st_x2:
            c.line(cx, beam_bot_y + 2, cx, beam_top_y - 2)
            cx += step_dense
    c.restoreState()

    # D. CỐT THÉP DỌC CHỊU LỰC: ĐẬM NÉT 0.50 MM (Màu Đỏ)
    # LƯU Ý PHẢN LỰC ĐẤT:
    # - Thép tăng cường NHỊP đặt ở LỚP TRÊN (LƯNG DẦM)!
    # - Thép tăng cường GỐI đặt ở LỚP DƯỚI (BỤNG DẦM)!
    c.saveState()
    c.setLineWidth(LW_REBAR_PT)
    c.setStrokeColorRGB(0.85, 0.1, 0.1)

    start_x = span_coords[0]["x1"] + 2.5
    end_x = span_coords[-1]["x2"] - 2.5
    main_top_y = beam_top_y - 3.5
    main_bot_y = beam_bot_y + 3.5

    # 1. Thép chủ trên chạy suốt liên tục
    c.line(start_x, main_top_y, end_x, main_top_y)
    # Bẻ ke neo 90 độ xuống cột biên
    c.line(start_x, main_top_y, start_x, main_top_y - 12)
    c.line(end_x, main_top_y, end_x, main_top_y - 12)

    # 2. Thép chủ dưới chạy suốt liên tục
    c.line(start_x, main_bot_y, end_x, main_bot_y)
    # Bẻ ke neo 90 độ lên cột biên
    c.line(start_x, main_bot_y, start_x, main_bot_y + 12)
    c.line(end_x, main_bot_y, end_x, main_bot_y + 12)

    # 3. THÉP TĂNG CƯỜNG NHỊP: BỐ TRÍ Ở LỚP TRÊN (LƯNG DẦM - do phản lực đất uốn cong vồng lên)
    # Vẽ nhích xuống 3pt so với thép chủ trên
    extra_top_y = main_top_y - 3.5
    for sc in span_coords:
        sp = sc["span"]
        if sp.get("extra_top_mid"):
            # Chiều dài cắt thép 0.65L ở giữa nhịp
            cut_l = sc["w"] * 0.18
            cut_r = sc["w"] * 0.82
            x_left = sc["x1"] + cut_l
            x_right = sc["x1"] + cut_r
            c.line(x_left, extra_top_y, x_right, extra_top_y)
            # Móc neo bẻ chúc xuống 45 độ ở 2 đầu
            c.line(x_left, extra_top_y, x_left + 4, extra_top_y - 3)
            c.line(x_right, extra_top_y, x_right - 4, extra_top_y - 3)

    # 4. THÉP TĂNG CƯỜNG GỐI: BỐ TRÍ Ở LỚP DƯỚI (BỤNG DẦM - do cột đè xuống chống áp lực đất)
    # Vẽ nhích lên 3pt so với thép chủ dưới
    extra_bot_y = main_bot_y + 3.5
    for i, sc in enumerate(span_coords):
        sp = sc["span"]
        l_quarter = sc["w"] * 0.25
        # Gối đầu tiên
        if i == 0 and sp.get("extra_bot_support"):
            c.line(sc["x1"] + 2.5, extra_bot_y, sc["x1"] + l_quarter, extra_bot_y)
            c.line(sc["x1"] + 2.5, extra_bot_y, sc["x1"] + 2.5, extra_bot_y + 8)
            c.line(sc["x1"] + l_quarter, extra_bot_y, sc["x1"] + l_quarter - 4, extra_bot_y + 3)

        # Các gối giữa liên tục
        if i < len(span_coords) - 1:
            next_q = span_coords[i+1]["w"] * 0.25
            c.line(sc["x2"] - l_quarter, extra_bot_y, sc["x2"] + next_q, extra_bot_y)
            c.line(sc["x2"] - l_quarter, extra_bot_y, sc["x2"] - l_quarter + 4, extra_bot_y + 3)
            c.line(sc["x2"] + next_q, extra_bot_y, sc["x2"] + next_q - 4, extra_bot_y + 3)
        else: # Gối cuối cùng
            if sp.get("extra_bot_support"):
                c.line(sc["x2"] - l_quarter, extra_bot_y, sc["x2"] - 2.5, extra_bot_y)
                c.line(sc["x2"] - 2.5, extra_bot_y, sc["x2"] - 2.5, extra_bot_y + 8)
                c.line(sc["x2"] - l_quarter, extra_bot_y, sc["x2"] - l_quarter + 4, extra_bot_y + 3)
    c.restoreState()

    # E. ĐƯỜNG KÍCH THƯỚC (Nét 0.09 mm)
    # 1. Dim nhịp dầm phía trên
    dim_top_y = beam_top_y + 11
    for sc in span_coords:
        draw_pdf_dim_line(c, sc["x1"], dim_top_y, sc["x2"], dim_top_y, f"{int(sc['len'])}")

    # 2. Dim chi tiết cắt thép tăng cường nhịp phía trên
    dim_extra_top_y = dim_top_y + 10
    for sc in span_coords:
        sp = sc["span"]
        if sp.get("extra_top_mid"):
            len_val = sc["len"]
            l1 = int(len_val * 0.18)
            l2 = int(len_val * 0.64)
            l3 = int(len_val) - l1 - l2
            xa = sc["x1"]
            xb = sc["x1"] + sc["w"] * 0.18
            xc = sc["x1"] + sc["w"] * 0.82
            xd = sc["x2"]
            draw_pdf_dim_line(c, xa, dim_extra_top_y, xb, dim_extra_top_y, f"{l1}")
            draw_pdf_dim_line(c, xb, dim_extra_top_y, xc, dim_extra_top_y, f"{l2} (Tăng cường nhịp)", is_bold=True)
            draw_pdf_dim_line(c, xc, dim_extra_top_y, xd, dim_extra_top_y, f"{l3}")

    # 3. Dim nhịp thông thủy bên dưới đài móng
    dim_span_y = beam_bot_y - 34
    for sc in span_coords:
        draw_pdf_dim_line(c, sc["x1"], dim_span_y, sc["x2"], dim_span_y, f"{int(sc['len'])}")

    # 4. ĐƯỜNG DIM TỔNG BÊN DƯỚI NGANG LƯỚI TRỤC
    dim_total_y = dim_span_y - 11
    draw_pdf_dim_line(c, span_coords[0]["x1"], dim_total_y, span_coords[-1]["x2"], dim_total_y, f"{int(total_len)}", is_bold=True)

    # F. TRỤC KIẾN TRÚC TRÒN
    bubble_y = dim_total_y - 12
    c.saveState()
    c.setLineWidth(LW_DEFAULT_PT)
    c.setStrokeColorRGB(0.4, 0.45, 0.55)
    c.setFont(FONT_BOLD, 6.5)
    c.setFillColorRGB(0.1, 0.2, 0.35)

    support_grids = axis_data["support_grids"]
    for i, sx in enumerate(support_xs):
        grid_lbl = support_grids[i] if i < len(support_grids) else f"{i+1}"
        c.circle(sx, bubble_y, 6.5, fill=1, stroke=1)
        c.setFillColorRGB(1, 1, 1)
        c.circle(sx, bubble_y, 5.8, fill=1, stroke=0)
        c.setFillColorRGB(0.1, 0.2, 0.35)
        c.drawCentredString(sx, bubble_y - 2.5, grid_lbl)
    c.restoreState()

    # G. VẼ CÁC MẶT CẮT NGANG ĐIỂN HÌNH (SECTION CROSS) BÊN PHẢI
    # Mặt cắt 1-1: Tại Nhịp (Mid-span) -> Thấy rõ thép tăng cường ở LƯNG DẦM
    # Mặt cắt 2-2: Tại Gối (Support) -> Thấy rõ thép tăng cường ở BỤNG DẦM
    sec_sp = spans[1] if len(spans) > 1 else spans[0]
    draw_tie_beam_cross_sections(c, cs_x, by + 10, cs_w, bh - 30, sec_sp, axis_data["axis_id"])


def draw_tie_beam_cross_sections(c, cs_x, cs_y, cs_w, cs_h, sec_data, axis_id):
    """
    Vẽ 2 mặt cắt ngang điển hình cho đà kiềng:
    - Mặt cắt 1-1 (TẠI GIỮA NHỊP): Căng thớ TRÊN do phản lực đất -> Thép tăng cường ở LƯNG DẦM.
    - Mặt cắt 2-2 (TẠI GỐI TỰA): Căng thớ DƯỚI do cột đè xuống -> Thép tăng cường ở BỤNG DẦM.
    """
    b_w = sec_data["width"]
    b_h = sec_data["depth"]

    # Phân chia thành 2 ô mặt cắt trên/dưới
    half_h = cs_h / 2.0

    # 1. MẶT CẮT 1-1: TẠI NHỊP (MID-SPAN)
    cs1_y = cs_y + half_h
    draw_single_cs(
        c, cs_x + 10, cs1_y + 5, cs_w - 20, half_h - 15,
        title=f"MẶT CẮT 1-1 (GIỮA NHỊP {axis_id})",
        sub_title="[CĂNG THỚ TRÊN DO PHẢN LỰC ĐẤT]",
        b_w=b_w, b_h=b_h,
        top_rebar=f"{sec_data['main_top']} + {sec_data.get('extra_top_mid', '')}".strip(" +"),
        bot_rebar=sec_data['main_bot'],
        stirrup=sec_data['stirrup'],
        is_mid_span=True
    )

    # 2. MẶT CẮT 2-2: TẠI GỐI TỰA (SUPPORT)
    cs2_y = cs_y
    draw_single_cs(
        c, cs_x + 10, cs2_y + 5, cs_w - 20, half_h - 15,
        title=f"MẶT CẮT 2-2 (GỐI CỘT {axis_id})",
        sub_title="[CĂNG THỚ DƯỚI DO CỘT TỰA ĐÈ XUỐNG]",
        b_w=b_w, b_h=b_h,
        top_rebar=sec_data['main_top'],
        bot_rebar=f"{sec_data['main_bot']} + {sec_data.get('extra_bot_support', '')}".strip(" +"),
        stirrup=sec_data['stirrup'],
        is_mid_span=False
    )


def draw_single_cs(c, x, y, w, h, title, sub_title, b_w, b_h, top_rebar, bot_rebar, stirrup, is_mid_span=True):
    """Vẽ chi tiết 1 mặt cắt ngang đà kiềng đúng phong cách kỹ thuật TCVN."""
    c.saveState()

    # Tiêu đề mặt cắt
    c.setFont(FONT_BOLD, 7.5)
    c.setFillColorRGB(0.1, 0.15, 0.3)
    c.drawCentredString(x + w / 2.0, y + h - 10, title)
    c.setFont(FONT_REGULAR, 6.0)
    c.setFillColorRGB(0.8, 0.3, 0.05 if is_mid_span else 0.1)
    c.drawCentredString(x + w / 2.0, y + h - 18, sub_title)

    # Tính tỉ lệ hình chữ nhật bê tông
    box_max_h = h - 45
    box_max_w = w * 0.45
    sc = min(box_max_w / b_w, box_max_h / b_h)
    draw_bw = b_w * sc
    draw_bh = b_h * sc
    bx = x + w * 0.32 - draw_bw / 2.0
    by = y + 16

    # Khung bê tông đà kiềng (Nét 0.15 mm)
    c.setLineWidth(LW_DEFAULT_PT)
    c.setStrokeColorRGB(0.15, 0.2, 0.3)
    c.setFillColorRGB(0.97, 0.98, 1.0)
    c.rect(bx, by, draw_bw, draw_bh, fill=1, stroke=1)

    # Cốt đai: lùi 35mm bê tông bảo vệ móng (tiếp xúc đất)
    cover_pt = 35.0 * sc
    stirrup_x = bx + cover_pt
    stirrup_y = by + cover_pt
    stirrup_w = draw_bw - cover_pt * 2
    stirrup_h = draw_bh - cover_pt * 2

    c.setLineWidth(LW_DEFAULT_PT)
    c.setStrokeColorRGB(0.02, 0.55, 0.8)
    c.roundRect(stirrup_x, stirrup_y, stirrup_w, stirrup_h, 2.5, stroke=1, fill=0)

    # Móc neo đai 135 độ ở góc trên trái
    c.line(stirrup_x + 3, stirrup_y + stirrup_h - 1, stirrup_x + 6, stirrup_y + stirrup_h - 4)
    c.line(stirrup_x + 1, stirrup_y + stirrup_h - 3, stirrup_x + 4, stirrup_y + stirrup_h - 6)

    # Phân tích số thanh thép trên / dưới
    def parse_bar_count(s):
        import re
        total = 0
        for m in re.finditer(r'(\d+)\s*[ΦdD]', s):
            total += int(m.group(1))
        return total if total > 0 else 2

    top_count = parse_bar_count(top_rebar)
    bot_count = parse_bar_count(bot_rebar)

    # Vẽ các thanh thép chấm tròn đỏ đậm nét 0.50 mm
    c.setFillColorRGB(0.85, 0.1, 0.1)
    c.setStrokeColorRGB(0.6, 0.05, 0.05)
    c.setLineWidth(0.4)
    dot_r = 2.4

    # Thép lớp trên
    if top_count == 2:
        top_xs = [stirrup_x + 3.0, stirrup_x + stirrup_w - 3.0]
    elif top_count == 3:
        top_xs = [stirrup_x + 3.0, stirrup_x + stirrup_w / 2.0, stirrup_x + stirrup_w - 3.0]
    elif top_count >= 4:
        dx = (stirrup_w - 6.0) / (top_count - 1)
        top_xs = [stirrup_x + 3.0 + i * dx for i in range(top_count)]
    else:
        top_xs = [stirrup_x + 3.0, stirrup_x + stirrup_w - 3.0]

    for tx in top_xs:
        c.circle(tx, stirrup_y + stirrup_h - 3.0, dot_r, fill=1, stroke=1)

    # Thép lớp dưới
    if bot_count == 2:
        bot_xs = [stirrup_x + 3.0, stirrup_x + stirrup_w - 3.0]
    elif bot_count == 3:
        bot_xs = [stirrup_x + 3.0, stirrup_x + stirrup_w / 2.0, stirrup_x + stirrup_w - 3.0]
    elif bot_count >= 4:
        dx = (stirrup_w - 6.0) / (bot_count - 1)
        bot_xs = [stirrup_x + 3.0 + i * dx for i in range(bot_count)]
    else:
        bot_xs = [stirrup_x + 3.0, stirrup_x + stirrup_w - 3.0]

    for bx_pos in bot_xs:
        c.circle(bx_pos, stirrup_y + 3.0, dot_r, fill=1, stroke=1)

    # Kích thước Dim b (bên dưới) & h (bên trái)
    dim_y = by - 7
    draw_pdf_dim_line(c, bx, dim_y, bx + draw_bw, dim_y, f"{int(b_w)}")

    dim_h_x = bx - 7
    c.setLineWidth(LW_DIM_PT)
    c.setStrokeColorRGB(0.1, 0.45, 0.25)
    c.line(dim_h_x, by, dim_h_x, by + draw_bh)
    c.line(dim_h_x - 2, by - 2, dim_h_x + 2, by + 2)
    c.line(dim_h_x - 2, by + draw_bh - 2, dim_h_x + 2, by + draw_bh + 2)
    c.setFont(FONT_REGULAR, 6.0)
    c.setFillColorRGB(0.1, 0.35, 0.2)
    c.saveState()
    c.translate(dim_h_x - 3, by + draw_bh / 2.0)
    c.rotate(90)
    c.drawCentredString(0, 0, f"{int(b_h)}")
    c.restoreState()

    # Leader chỉ thép lớp trên
    lead_x = bx + draw_bw + 8
    lead_top_y = stirrup_y + stirrup_h + 2
    c.setLineWidth(LW_DEFAULT_PT)
    c.setStrokeColorRGB(0.3, 0.35, 0.45)
    c.line(top_xs[-1], stirrup_y + stirrup_h - 3.0, lead_x, lead_top_y)
    c.line(lead_x, lead_top_y, lead_x + 40, lead_top_y)
    c.setFont(FONT_BOLD, 6.5)
    c.setFillColorRGB(0.85, 0.1, 0.1)
    c.drawString(lead_x + 2, lead_top_y + 2, f"{top_rebar}")
    if is_mid_span:
        c.setFont(FONT_REGULAR, 5.0)
        c.setFillColorRGB(0.8, 0.35, 0.05)
        c.drawString(lead_x + 2, lead_top_y - 6, "(Thép tăng cường lưng nhịp)")

    # Leader chỉ thép lớp dưới
    lead_bot_y = stirrup_y - 2
    c.line(bot_xs[-1], stirrup_y + 3.0, lead_x, lead_bot_y)
    c.line(lead_x, lead_bot_y, lead_x + 40, lead_bot_y)
    c.setFont(FONT_BOLD, 6.5)
    c.setFillColorRGB(0.85, 0.1, 0.1)
    c.drawString(lead_x + 2, lead_bot_y + 2, f"{bot_rebar}")
    if not is_mid_span:
        c.setFont(FONT_REGULAR, 5.0)
        c.setFillColorRGB(0.8, 0.35, 0.05)
        c.drawString(lead_x + 2, lead_bot_y - 6, "(Thép tăng cường bụng gối)")

    # Leader đai
    lead_stirrup_y = by + draw_bh * 0.5
    c.line(stirrup_x + stirrup_w, lead_stirrup_y, lead_x, lead_stirrup_y)
    c.line(lead_x, lead_stirrup_y, lead_x + 35, lead_stirrup_y)
    c.setFont(FONT_REGULAR, 6.0)
    c.setFillColorRGB(0.02, 0.5, 0.75)
    c.drawString(lead_x + 2, lead_stirrup_y + 2, f"{stirrup}")

    c.restoreState()


def generate_tie_beam_pdf(output_path=None):
    """
    Tạo toàn bộ file PDF bản vẽ chi tiết Đà Kiềng Trục A, B, C (Khổ A1 landscape).
    Áp dụng triệt để nguyên lý PHẢN LỰC ĐẤT ĐẨY LÊN.
    """
    buffer = io.BytesIO() if output_path is None else None
    c = canvas.Canvas(output_path if output_path else buffer, pagesize=landscape(A1))

    # Lề bản vẽ A1 (20mm lề trái để đóng gáy, 10mm các lề còn lại)
    m_left = 25.0 * MM_TO_PT
    m_right = 15.0 * MM_TO_PT
    m_top = 15.0 * MM_TO_PT
    m_bottom = 15.0 * MM_TO_PT

    frame_x = m_left
    frame_y = m_bottom
    frame_w = SHEET_W_PT - m_left - m_right
    frame_h = SHEET_H_PT - m_top - m_bottom

    # 1. Khung bản vẽ A1 CAD đôi
    c.saveState()
    c.setLineWidth(LW_BORDER_PT)
    c.setStrokeColorRGB(0.1, 0.15, 0.25)
    c.rect(frame_x, frame_y, frame_w, frame_h)
    c.setLineWidth(LW_DEFAULT_PT)
    c.rect(frame_x + 5, frame_y + 5, frame_w - 10, frame_h - 10)

    # 2. Tiêu đề lớn đầu trang
    c.setFont(FONT_BOLD, 15)
    c.setFillColorRGB(0.05, 0.12, 0.28)
    c.drawString(frame_x + 15, frame_y + frame_h - 24, "BẢN VẼ CHI TIẾT ĐÀ KIỀNG DỌC THEO TRỤC A, B, C (TẦNG 1 / MÓNG)")
    c.setFont(FONT_REGULAR, 8.5)
    c.setFillColorRGB(0.35, 0.4, 0.5)
    c.drawString(frame_x + 15, frame_y + frame_h - 37, "DỰ ÁN: CẢI TẠO PHƯƠNG ÁN B • TCVN 5574:2018 • BỐ TRÍ THÉP XÉT ĐẾN TÁC ĐỘNG CỦA PHẢN LỰC ĐẤT NỀN ĐẨY LÊN")
    c.restoreState()

    # 3. Lấy dữ liệu 3 tuyến đà kiềng
    data = get_tie_beam_data()
    axes = data["axes"]

    # Phân chia chiều cao cho 3 tuyến đà kiềng + phần ghi chú kỹ thuật bên dưới (Không cần khung tên)
    bottom_section_h = 52.0
    content_y = frame_y + bottom_section_h + 10
    content_h = frame_h - bottom_section_h - 55

    # Mỗi tuyến đà kiềng chiếm 1/3 chiều cao
    axis_h = content_h / 3.0

    # Tuyến Trục A (ở trên cùng)
    draw_elevation_axis(c, axes[0], frame_x + 8, content_y + axis_h * 2, frame_w - 16, axis_h)

    # Đường phân cách nét đứt nhẹ giữa Trục A và Trục B
    c.saveState()
    c.setLineWidth(0.5)
    c.setStrokeColorRGB(0.8, 0.85, 0.9)
    c.setDash(4, 4)
    c.line(frame_x + 15, content_y + axis_h * 2, frame_x + frame_w - 15, content_y + axis_h * 2)
    c.restoreState()

    # Tuyến Trục B (ở giữa)
    draw_elevation_axis(c, axes[1], frame_x + 8, content_y + axis_h * 1, frame_w - 16, axis_h)

    # Đường phân cách nét đứt nhẹ giữa Trục B và Trục C
    c.saveState()
    c.setLineWidth(0.5)
    c.setStrokeColorRGB(0.8, 0.85, 0.9)
    c.setDash(4, 4)
    c.line(frame_x + 15, content_y + axis_h * 1, frame_x + frame_w - 15, content_y + axis_h * 1)
    c.restoreState()

    # Tuyến Trục C (ở dưới)
    draw_elevation_axis(c, axes[2], frame_x + 8, content_y, frame_w - 16, axis_h)

    # 4. KHU VỰC DƯỚI: GHI CHÚ KỸ THUẬT (TRẢI RỘNG TOÀN KHỔ, KHÔNG CẦN KHUNG TÊN)
    notes_w = frame_w - 16
    tb_y = frame_y + 8

    # Ghi chú kỹ thuật về phản lực đất (General Technical Notes)
    c.saveState()
    c.setLineWidth(LW_DEFAULT_PT)
    c.setStrokeColorRGB(0.8, 0.85, 0.9)
    c.setFillColorRGB(0.98, 0.99, 1.0)
    c.rect(frame_x + 8, tb_y, notes_w, bottom_section_h, fill=1, stroke=1)

    c.setFont(FONT_BOLD, 7.5)
    c.setFillColorRGB(0.8, 0.2, 0.05)
    c.drawString(frame_x + 16, tb_y + bottom_section_h - 12, "★ GHI CHÚ NGUYÊN LÝ BỐ TRÍ THÉP ĐÀ KIỀNG CHỊU PHẢN LỰC ĐẤT NỀN ĐẨY LÊN (TCVN 5574:2018):")

    c.setFont(FONT_REGULAR, 6.4)
    c.setFillColorRGB(0.15, 0.2, 0.3)
    col1_w = notes_w * 0.52
    line_y = tb_y + bottom_section_h - 23
    for i, n in enumerate(data["notes"]):
        if i < 3:
            c.drawString(frame_x + 16, line_y - i * 9.5, f"• {n}")
        else:
            c.drawString(frame_x + 16 + col1_w, line_y - (i - 3) * 9.5, f"• {n}")
    c.restoreState()

    c.showPage()
    c.save()

    if output_path:
        return output_path
    buffer.seek(0)
    return buffer.getvalue()


def generate_tie_beam_dxf(output_path=None):
    """
    Xuất bản vẽ chi tiết Đà Kiềng Trục A, B, C sang định dạng AutoCAD R2010 DXF.
    Phân chia layer tiêu chuẩn: BE_TONG, THEP_CHU, COT_DAI, DIM, TEXT, KHUNG_TEN, PHAN_LUC_DAT.
    """
    doc = get_template_dxf_doc()
    msp = doc.modelspace()

    # Thiết lập layers
    layers = [
        ("BE_TONG", 7, 0.15, "Continuous"),       # Trắng/Đen
        ("THEP_CHU", 1, 0.50, "Continuous"),      # Đỏ
        ("COT_DAI", 4, 0.15, "Continuous"),       # Cyan
        ("DIM", 3, 0.09, "Continuous"),           # Xanh lá
        ("TEXT", 7, 0.15, "Continuous"),          # Trắng
        ("KHUNG_TEN", 7, 0.35, "Continuous"),     # Trắng nét đậm
        ("PHAN_LUC_DAT", 30, 0.20, "Continuous"), # Cam
        ("TRUC", 8, 0.15, "CENTER")           # Xám nét trục
    ]
    for l_name, color, lw, l_type in layers:
        ensure_layer(doc, l_name, color=color, lineweight=int(lw * 100), linetype=l_type)

    data = get_tie_beam_data()
    axes = data["axes"]

    # Đơn vị trong DXF là mm thực tế (1:1), bố trí 3 tuyến cách nhau theo trục Y
    base_y = 0.0
    for ax_idx, ax in enumerate(axes):
        spans = ax["spans"]
        y_elev = base_y + ax_idx * 6000.0

        # Tiêu đề tuyến
        msp.add_text(
            f"{ax['axis_title']} - CAO ĐỘ +1.800 (TẦNG 1 / MÓNG) - L = {ax['total_len_mm']:.0f}mm",
            dxfattribs={"layer": "TEXT", "height": 220}
        ).set_placement((0.0, y_elev + 1800.0))

        # Vẽ từng nhịp dầm
        cur_x = 0.0
        for sp in spans:
            l_mm = sp["length"]
            d_mm = sp["depth"]
            w_mm = sp["width"]

            # Khung bê tông dầm
            p_bot_left = (cur_x, y_elev)
            p_top_left = (cur_x, y_elev + d_mm)
            p_top_right = (cur_x + l_mm, y_elev + d_mm)
            p_bot_right = (cur_x + l_mm, y_elev)
            msp.add_lwpolyline([p_bot_left, p_top_left, p_top_right, p_bot_right, p_bot_left], dxfattribs={"layer": "BE_TONG"})

            # Cổ cột bên dưới
            msp.add_lwpolyline([
                (cur_x - 150, y_elev), (cur_x - 150, y_elev - 500),
                (cur_x + 150, y_elev - 500), (cur_x + 150, y_elev)
            ], dxfattribs={"layer": "BE_TONG"})

            # Mũi tên phản lực đất đẩy lên (q_đất)
            arr_step = 1200.0
            cx_arr = cur_x + 600.0
            while cx_arr < cur_x + l_mm - 300.0:
                msp.add_line((cx_arr, y_elev - 400), (cx_arr, y_elev - 50), dxfattribs={"layer": "PHAN_LUC_DAT"})
                msp.add_lwpolyline([
                    (cx_arr - 60, y_elev - 150), (cx_arr, y_elev - 50), (cx_arr + 60, y_elev - 150)
                ], dxfattribs={"layer": "PHAN_LUC_DAT"})
                cx_arr += arr_step

            # Thép chủ trên (lưng dầm)
            msp.add_line((cur_x, y_elev + d_mm - 40), (cur_x + l_mm, y_elev + d_mm - 40), dxfattribs={"layer": "THEP_CHU"})

            # Thép chủ dưới (bụng dầm)
            msp.add_line((cur_x, y_elev + 40), (cur_x + l_mm, y_elev + 40), dxfattribs={"layer": "THEP_CHU"})

            # THÉP TĂNG CƯỜNG NHỊP: BỐ TRÍ Ở LƯNG DẦM (LỚP TRÊN) do phản lực đất
            if sp.get("extra_top_mid"):
                x_extra_start = cur_x + l_mm * 0.18
                x_extra_end = cur_x + l_mm * 0.82
                msp.add_line((x_extra_start, y_elev + d_mm - 80), (x_extra_end, y_elev + d_mm - 80), dxfattribs={"layer": "THEP_CHU"})
                msp.add_line((x_extra_start, y_extra_start := y_elev + d_mm - 80), (x_extra_start + 80, y_extra_start - 60), dxfattribs={"layer": "THEP_CHU"})
                msp.add_line((x_extra_end, y_extra_start), (x_extra_end - 80, y_extra_start - 60), dxfattribs={"layer": "THEP_CHU"})
                # Text chỉ thép
                msp.add_text(f"TC Nhịp (Lưng): {sp['extra_top_mid']}", dxfattribs={"layer": "TEXT", "height": 110}).set_placement((cur_x + l_mm * 0.35, y_elev + d_mm - 120))

            # THÉP TĂNG CƯỜNG GỐI: BỐ TRÍ Ở BỤNG DẦM (LỚP DƯỚI) do cột đè xuống
            if sp.get("extra_bot_support"):
                q_len = l_mm * 0.25
                msp.add_line((cur_x, y_elev + 80), (cur_x + q_len, y_elev + 80), dxfattribs={"layer": "THEP_CHU"})
                msp.add_line((cur_x + l_mm - q_len, y_elev + 80), (cur_x + l_mm, y_elev + 80), dxfattribs={"layer": "THEP_CHU"})
                msp.add_text(f"TC Gối (Bụng): {sp['extra_bot_support']}", dxfattribs={"layer": "TEXT", "height": 110}).set_placement((cur_x + 100, y_elev + 110))

            # Dim nhịp dầm
            msp.add_line((cur_x, y_elev + d_mm + 250), (cur_x + l_mm, y_elev + d_mm + 250), dxfattribs={"layer": "DIM"})
            msp.add_text(f"{l_mm:.0f}", dxfattribs={"layer": "DIM", "height": 120}).set_placement((cur_x + l_mm / 2.0 - 150, y_elev + d_mm + 280))

            cur_x += l_mm

        # Trục kiến trúc bên dưới
        support_grids = ax["support_grids"]
        cx_grid = 0.0
        for gi, sp in enumerate(spans):
            grid_lbl = support_grids[gi] if gi < len(support_grids) else f"{gi+1}"
            msp.add_circle((cx_grid, y_elev - 1000), 250, dxfattribs={"layer": "TRUC"})
            msp.add_text(grid_lbl, dxfattribs={"layer": "TEXT", "height": 180}).set_placement((cx_grid - 60, y_elev - 1060))
            cx_grid += sp["length"]

        # Trục cuối cùng
        last_lbl = support_grids[-1] if len(support_grids) > len(spans) else f"{len(spans)+1}"
        msp.add_circle((cx_grid, y_elev - 1000), 250, dxfattribs={"layer": "TRUC"})
        msp.add_text(last_lbl, dxfattribs={"layer": "TEXT", "height": 180}).set_placement((cx_grid - 60, y_elev - 1060))

    if output_path:
        doc.saveas(output_path)
        return output_path
    
    stream = io.StringIO()
    doc.write(stream)
    return stream.getvalue().encode("utf-8")


if __name__ == "__main__":
    pdf_out = "test_tie_beam_sheet.pdf"
    dxf_out = "test_tie_beam_sheet.dxf"
    generate_tie_beam_pdf(pdf_out)
    generate_tie_beam_dxf(dxf_out)
    print(f"Generated PDF: {pdf_out} ({os.path.getsize(pdf_out):,} bytes)")
    print(f"Generated DXF: {dxf_out} ({os.path.getsize(dxf_out):,} bytes)")
