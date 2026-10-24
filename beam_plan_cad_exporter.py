#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
beam_plan_cad_exporter.py
Bộ xuất bản vẽ kỹ thuật CAD Mặt Bằng Ký Hiệu Dầm (Beam Framing Layout Plan).
Định dạng xuất: PDF (vector chuẩn TCVN) và DXF (AutoCAD R2010).
Hỗ trợ tất cả các tầng: DK (Đà kiềng), T1, T2, T3, T4.
Theo yêu cầu người dùng: Không vẽ title block ở góc, dầm thể hiện đúng bề rộng và ký hiệu dầm.
"""

import os
import io
import math
import json
import re
from reportlab.lib.pagesizes import A1, landscape
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
        print(f"[BeamPlanExporter] Không thể nạp font Arial: {e}")

FONT_REGULAR = "Arial" if HAS_ARIAL else "Helvetica"
FONT_BOLD = "Arial-Bold" if HAS_ARIAL else "Helvetica-Bold"

MM_TO_PT = 72.0 / 25.4

# Chiều dày nét in PDF chuẩn
LW_THICK_PT = 0.35 * MM_TO_PT
LW_MEDIUM_PT = 0.20 * MM_TO_PT
LW_THIN_PT = 0.09 * MM_TO_PT

# Khổ giấy A1 Landscape (841 x 594 mm)
SHEET_W_MM = 841.0
SHEET_H_MM = 594.0
SHEET_W_PT = SHEET_W_MM * MM_TO_PT
SHEET_H_PT = SHEET_H_MM * MM_TO_PT

STORY_TITLES = {
    "DK": ("MẶT BẰNG ĐỊNH VỊ ĐÀ KIỀNG (MÓNG)", "+1.800"),
    "T1": ("MẶT BẰNG KÝ HIỆU DẦM SÀN TẦNG 1", "+1.800"),
    "T2": ("MẶT BẰNG KÝ HIỆU DẦM SÀN TẦNG 2", "+7.600"),
    "T3": ("MẶT BẰNG KÝ HIỆU DẦM SÀN TẦNG 3", "+11.800"),
    "T4": ("MẶT BẰNG KÝ HIỆU DẦM SÀN TẦNG 4", "+15.600"),
    "C":  ("MẶT BẰNG ĐỊNH VỊ VÀ BỐ TRÍ CỘT TOÀN NHÀ", "±0.000")
}


def get_beam_plan_data(story="T3", etabs_data=None):
    """Trích xuất dầm, cột và hệ lưới trục theo tầng đã chọn."""
    if etabs_data is None:
        try:
            import etabs_service
            etabs_data = etabs_service.get_etabs_data()
        except Exception:
            try:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                with open(os.path.join(base_dir, "etabs_beam_data.json"), "r", encoding="utf-8") as f:
                    etabs_data = json.load(f)
            except Exception:
                etabs_data = {}

    grids_x = etabs_data.get("grids", {}).get("X", [])
    grids_y = etabs_data.get("grids", {}).get("Y", [])
    all_beams = etabs_data.get("beams", [])
    all_cols = etabs_data.get("columns", [])

    # Story mapping: 'DK' dùng story 'T1'
    filter_story = "T1" if story == "DK" else story

    story_beams = [b for b in all_beams if b.get("story") == filter_story]
    story_cols = [c for c in all_cols if c.get("story") == filter_story]
    if not story_cols and filter_story == "T1":
        story_cols = [c for c in all_cols if c.get("story") == "T1"]

    return {
        "story": story,
        "grids_x": grids_x,
        "grids_y": grids_y,
        "beams": story_beams,
        "columns": story_cols
    }


def draw_bubble_pdf(canv, x_pt, y_pt, label, r_pt=12.0):
    """Vẽ bóng tròn trục tròn chuẩn CAD."""
    canv.saveState()
    canv.setFillColorRGB(1.0, 1.0, 1.0)
    canv.setStrokeColorRGB(0.15, 0.25, 0.4)
    canv.setLineWidth(LW_THICK_PT)
    canv.circle(x_pt, y_pt, r_pt, fill=1, stroke=1)
    canv.setFont(FONT_BOLD, 9.5)
    canv.setFillColorRGB(0.08, 0.15, 0.25)
    canv.drawCentredString(x_pt, y_pt - 3.5, str(label))
    canv.restoreState()


def draw_dim_line_pdf(canv, x1_pt, y1_pt, x2_pt, y2_pt, dim_text, is_vertical=False):
    """Vẽ đường kích thước kèm vạch gạch chéo 45 độ chuẩn TCVN."""
    canv.saveState()
    canv.setStrokeColorRGB(0.15, 0.5, 0.2)
    canv.setLineWidth(LW_THIN_PT)
    canv.line(x1_pt, y1_pt, x2_pt, y2_pt)

    tick = 3.5
    canv.line(x1_pt - tick, y1_pt - tick, x1_pt + tick, y1_pt + tick)
    canv.line(x2_pt - tick, y2_pt - tick, x2_pt + tick, y2_pt + tick)

    canv.setFont(FONT_REGULAR, 7.5)
    canv.setFillColorRGB(0.1, 0.4, 0.15)
    if is_vertical:
        canv.saveState()
        canv.translate((x1_pt + x2_pt)/2.0 - 5.0, (y1_pt + y2_pt)/2.0)
        canv.rotate(90)
        canv.drawCentredString(0, 0, str(dim_text))
        canv.restoreState()
    else:
        canv.drawCentredString((x1_pt + x2_pt)/2.0, y1_pt + 3.0, str(dim_text))
    canv.restoreState()


def generate_beam_plan_pdf(output_path=None, story="T3"):
    """
    Sinh bản vẽ PDF A1 Landscape Mặt Bằng Ký Hiệu Dầm.
    Theo yêu cầu #3: KHÔNG vẽ title block ở góc để bản vẽ thoáng, rộng rãi nhất.
    """
    data = get_beam_plan_data(story=story)
    buf = io.BytesIO() if output_path is None else None
    target = output_path if output_path else buf

    canv = canvas.Canvas(target, pagesize=landscape(A1))
    title_info = STORY_TITLES.get(story, (f"MẶT BẰNG KÝ HIỆU DẦM ({story})", "+0.000"))
    canv.setTitle(f"BAN VE MAT BANG KY HIEU DAM - {story} - REVITAI STUDIO")

    # 1. Khung bản vẽ TCVN & Border (Không title block)
    margin_l = 25.0 * MM_TO_PT
    margin_r = 15.0 * MM_TO_PT
    margin_t = 15.0 * MM_TO_PT
    margin_b = 15.0 * MM_TO_PT

    canv.setStrokeColorRGB(0.1, 0.15, 0.25)
    canv.setLineWidth(LW_THICK_PT)
    canv.rect(margin_l, margin_b, SHEET_W_PT - margin_l - margin_r, SHEET_H_PT - margin_t - margin_b)

    # 2. Tiêu đề chính trang vẽ
    canv.setFont(FONT_BOLD, 18)
    canv.setFillColorRGB(0.08, 0.15, 0.3)
    canv.drawString(margin_l + 20, SHEET_H_PT - margin_t - 32, f"{title_info[0]} • CAO ĐỘ {title_info[1]}")
    canv.setFont(FONT_REGULAR, 10)
    canv.setFillColorRGB(0.35, 0.45, 0.55)
    canv.drawString(margin_l + 20, SHEET_H_PT - margin_t - 48, f"DỰ ÁN: CẢI TẠO PHƯƠNG ÁN B • TIÊU CHUẨN: TCVN 5574:2018 • BỐ TRÍ DẦM THEO ĐÚNG BỀ RỘNG VÀ KÝ HIỆU (DX / DY)")

    # 3. Thiết lập khung tọa độ vẽ Mặt Bằng (Tận dụng toàn bộ diện tích trang in)
    ext = 65.0
    plan_x = margin_l + 70.0
    plan_y = margin_b + 55.0
    plan_w = SHEET_W_PT - margin_l - margin_r - 140.0
    plan_h = SHEET_H_PT - margin_t - margin_b - 130.0

    scale_x = (plan_w - ext * 2 - 40.0) / 32950.0
    scale_y = (plan_h - ext * 2 - 40.0) / 11970.0
    scale = min(scale_x, scale_y)

    actual_draw_w = 32950.0 * scale
    actual_draw_h = 11970.0 * scale
    origin_x = plan_x + ext + 20.0 + ((plan_w - ext * 2 - 40.0) - actual_draw_w) / 2.0
    origin_y = plan_y + ext + 20.0 + ((plan_h - ext * 2 - 40.0) - actual_draw_h) / 2.0

    def to_pt(gx_mm, gy_mm):
        return origin_x + gx_mm * scale, origin_y + gy_mm * scale

    grids_x = data["grids_x"]
    grids_y = data["grids_y"]
    beams = data["beams"]
    columns = data["columns"]

    min_pt_x, min_pt_y = to_pt(0, 0)
    max_pt_x, max_pt_y = to_pt(32950, 11970)

    # 4. Vẽ các đường lưới trục (Grid Lines)
    canv.saveState()
    canv.setStrokeColorRGB(0.35, 0.40, 0.48)
    canv.setLineWidth(LW_THIN_PT)
    canv.setDash(5, 3)

    for gx in grids_x:
        px, _ = to_pt(gx["ordinate"], 0)
        canv.line(px, min_pt_y - ext, px, max_pt_y + ext)
        draw_bubble_pdf(canv, px, min_pt_y - ext - 12.0, gx["id"])
        draw_bubble_pdf(canv, px, max_pt_y + ext + 12.0, gx["id"])

    for gy in grids_y:
        _, py = to_pt(0, gy["ordinate"])
        canv.line(min_pt_x - ext, py, max_pt_x + ext, py)
        draw_bubble_pdf(canv, min_pt_x - ext - 12.0, py, gy["id"])
        draw_bubble_pdf(canv, max_pt_x + ext + 12.0, py, gy["id"])

    canv.restoreState()

    # 5. Chuỗi kích thước (Dimensions)
    # Kích thước từng nhịp X (bên dưới)
    for i in range(len(grids_x) - 1):
        x1_m = grids_x[i]["ordinate"]
        x2_m = grids_x[i+1]["ordinate"]
        px1, _ = to_pt(x1_m, 0)
        px2, _ = to_pt(x2_m, 0)
        dim_val = int(round(x2_m - x1_m))
        draw_dim_line_pdf(canv, px1, min_pt_y - ext - 34.0, px2, min_pt_y - ext - 34.0, str(dim_val))

    draw_dim_line_pdf(canv, min_pt_x, min_pt_y - ext - 50.0, max_pt_x, min_pt_y - ext - 50.0, "32950")

    # Kích thước từng nhịp Y (bên trái)
    for j in range(len(grids_y) - 1):
        y1_m = grids_y[j]["ordinate"]
        y2_m = grids_y[j+1]["ordinate"]
        _, py1 = to_pt(0, y1_m)
        _, py2 = to_pt(0, y2_m)
        dim_val = int(round(y2_m - y1_m))
        draw_dim_line_pdf(canv, min_pt_x - ext - 34.0, py1, min_pt_x - ext - 34.0, py2, str(dim_val), is_vertical=True)

    draw_dim_line_pdf(canv, min_pt_x - ext - 50.0, min_pt_y, min_pt_x - ext - 50.0, max_pt_y, "11970", is_vertical=True)

    # 6. VẼ DẦM THEO ĐÚNG BỀ RỘNG VÀ HƯỚNG
    canv.saveState()
    for b in beams:
        p1 = b["p1"]
        p2 = b["p2"]
        x1, y1 = to_pt(p1[0], p1[1])
        x2, y2 = to_pt(p2[0], p2[1])

        dx = x2 - x1
        dy = y2 - y1
        length_pt = math.sqrt(dx*dx + dy*dy)
        if length_pt < 1:
            continue

        b_width_mm = b.get("width", 200.0)
        hw_pt = (b_width_mm * scale) / 2.0

        nx = -dy / length_pt
        ny = dx / length_pt

        # 4 đỉnh dầm theo đúng bề rộng
        v1 = (x1 - hw_pt * nx, y1 - hw_pt * ny)
        v2 = (x1 + hw_pt * nx, y1 + hw_pt * ny)
        v3 = (x2 + hw_pt * nx, y2 + hw_pt * ny)
        v4 = (x2 - hw_pt * nx, y2 - hw_pt * ny)

        # Đổ màu dầm: Dầm 300 xanh đậm hơn, dầm 200 xanh thanh nhã
        if b_width_mm >= 300:
            canv.setFillColorRGB(0.85, 0.93, 1.0)
            canv.setStrokeColorRGB(0.05, 0.45, 0.75)
        else:
            canv.setFillColorRGB(0.92, 0.96, 1.0)
            canv.setStrokeColorRGB(0.15, 0.55, 0.85)

        canv.setLineWidth(1.0)
        p = canv.beginPath()
        p.moveTo(v1[0], v1[1])
        p.lineTo(v2[0], v2[1])
        p.lineTo(v3[0], v3[1])
        p.lineTo(v4[0], v4[1])
        p.close()
        canv.drawPath(p, fill=1, stroke=1)

        # Tim dầm nét đứt mảnh
        canv.setStrokeColorRGB(0.3, 0.45, 0.6)
        canv.setLineWidth(0.5)
        canv.setDash(2, 2)
        canv.line(x1, y1, x2, y2)
        canv.setDash()

        # 7. Nhãn ký hiệu dầm (VD: DX1: 200x400 hoặc DY2: 300x500)
        mid_x = (x1 + x2) / 2.0
        mid_y = (y1 + y2) / 2.0
        l_id = b.get("long_beam_id") or b.get("label", "B")
        sec_str = b.get("section", "200x400").replace("B ", "")
        label_text = f"{l_id}: {sec_str}"

        is_dy = abs(dy) > abs(dx)

        canv.saveState()
        canv.translate(mid_x, mid_y)
        if is_dy:
            canv.rotate(90)

        # Khung pill nền trắng mờ sau text để chữ luôn nổi bật, không bị tim dầm che
        text_w = canv.stringWidth(label_text, FONT_BOLD, 7.5)
        canv.setFillColorRGB(1.0, 1.0, 1.0)
        canv.setStrokeColorRGB(0.2, 0.4, 0.6)
        canv.setLineWidth(0.6)
        canv.roundRect(-text_w/2.0 - 3, -5.5, text_w + 6, 11, 2, fill=1, stroke=1)

        canv.setFont(FONT_BOLD, 7.5)
        canv.setFillColorRGB(0.05, 0.15, 0.35)
        canv.drawCentredString(0, -2.5, label_text)
        canv.restoreState()

    canv.restoreState()

    # 8. VẼ CỘT (ĐẬM NÉT BÊ TÔNG 0.35 MM)
    canv.saveState()
    for col in columns:
        p1 = col["p1"]
        cx, cy = to_pt(p1[0], p1[1])
        cw = (col.get("width", 300.0)) * scale
        cd = (col.get("depth", 300.0)) * scale

        canv.setFillColorRGB(0.12, 0.16, 0.24)
        canv.setStrokeColorRGB(0.05, 0.08, 0.12)
        canv.setLineWidth(LW_THICK_PT)
        canv.rect(cx - cw/2.0, cy - cd/2.0, cw, cd, fill=1, stroke=1)

        # Tim cột gạch chéo trắng mảnh
        canv.setStrokeColorRGB(1.0, 1.0, 1.0)
        canv.setLineWidth(0.4)
        canv.line(cx - cw/2.0 + 0.5, cy, cx + cw/2.0 - 0.5, cy)
        canv.line(cx, cy - cd/2.0 + 0.5, cx, cy + cd/2.0 - 0.5)

    canv.restoreState()

    # 9. Ghi chú kỹ thuật góc dưới bên trái (KHÔNG CÓ TITLE BLOCK theo yêu cầu #3)
    canv.saveState()
    canv.setFont(FONT_BOLD, 8.5)
    canv.setFillColorRGB(0.15, 0.2, 0.3)
    canv.drawString(margin_l + 20, margin_b + 32, "★ CHÚ DẪN MẶT BẰNG KÝ HIỆU DẦM KẾT CẤU (TCVN 5574:2018):")
    canv.setFont(FONT_REGULAR, 7.5)
    canv.setFillColorRGB(0.3, 0.35, 0.45)
    canv.drawString(margin_l + 20, margin_b + 20, "1. Ký hiệu dầm: DX (Dầm phương X chạy dọc nhà) • DY (Dầm phương Y chạy ngang nhà).")
    canv.drawString(margin_l + 20, margin_b + 10, "2. Tất cả thép đai dầm và cột quy chuẩn về Φ6 (d6a100/200). Bê tông dầm sàn B22.5 (M300).")
    canv.restoreState()

    canv.save()
    if output_path:
        return output_path
    return buf.getvalue()


def generate_beam_plan_dxf(output_path=None, story="T3"):
    """
    Sinh bản vẽ AutoCAD DXF (R2010) cho Mặt Bằng Ký Hiệu Dầm.
    """
    data = get_beam_plan_data(story=story)
    doc = get_template_dxf_doc()
    doc.header['$INSUNITS'] = 4 # mm
    msp = doc.modelspace()

    layers = [
        ('GRID_AXIS', 8, 'DASHDOT'),
        ('DIMENSIONS', 3, 'Continuous'),
        ('COLUMN_CONCRETE', 7, 'Continuous'),
        ('BEAM_OUTLINE', 4, 'Continuous'),      # Cyan
        ('BEAM_CENTERLINE', 9, 'DASHED'),   # Xám mờ dashed
        ('BEAM_TEXT', 2, 'Continuous'),         # Vàng Yellow
        ('TITLE_TEXT', 7, 'Continuous')
    ]
    for l_name, l_col, l_type in layers:
        ensure_layer(doc, l_name, color=l_col, linetype=l_type)

    grids_x = data["grids_x"]
    grids_y = data["grids_y"]
    beams = data["beams"]
    columns = data["columns"]

    ext = 1800.0
    # 1. Trục
    for gx in grids_x:
        x_val = gx["ordinate"]
        msp.add_line((x_val, -ext), (x_val, 11970.0 + ext), dxfattribs={'layer': 'GRID_AXIS', 'linetype': 'DASHDOT'})
        msp.add_circle((x_val, -ext - 450), radius=380, dxfattribs={'layer': 'GRID_AXIS'})
        msp.add_text(gx["id"], height=300, dxfattribs={'layer': 'GRID_AXIS'}).set_placement((x_val, -ext - 560), align=TextEntityAlignment.CENTER)
        msp.add_circle((x_val, 11970.0 + ext + 450), radius=380, dxfattribs={'layer': 'GRID_AXIS'})
        msp.add_text(gx["id"], height=300, dxfattribs={'layer': 'GRID_AXIS'}).set_placement((x_val, 11970.0 + ext + 340), align=TextEntityAlignment.CENTER)

    for gy in grids_y:
        y_val = gy["ordinate"]
        msp.add_line((-ext, y_val), (32950.0 + ext, y_val), dxfattribs={'layer': 'GRID_AXIS', 'linetype': 'DASHDOT'})
        msp.add_circle((-ext - 450, y_val), radius=380, dxfattribs={'layer': 'GRID_AXIS'})
        msp.add_text(gy["id"], height=300, dxfattribs={'layer': 'GRID_AXIS'}).set_placement((-ext - 560, y_val - 110), align=TextEntityAlignment.CENTER)
        msp.add_circle((32950.0 + ext + 450, y_val), radius=380, dxfattribs={'layer': 'GRID_AXIS'})
        msp.add_text(gy["id"], height=300, dxfattribs={'layer': 'GRID_AXIS'}).set_placement((32950.0 + ext + 340, y_val - 110), align=TextEntityAlignment.CENTER)

    # 2. Dim
    for i in range(len(grids_x) - 1):
        x1_v = grids_x[i]["ordinate"]
        x2_v = grids_x[i+1]["ordinate"]
        dim_str = str(int(round(x2_v - x1_v)))
        msp.add_line((x1_v, -ext - 1100), (x2_v, -ext - 1100), dxfattribs={'layer': 'DIMENSIONS'})
        msp.add_text(dim_str, height=220, dxfattribs={'layer': 'DIMENSIONS'}).set_placement(((x1_v + x2_v)/2.0, -ext - 980), align=TextEntityAlignment.CENTER)

    msp.add_line((0, -ext - 1700), (32950, -ext - 1700), dxfattribs={'layer': 'DIMENSIONS'})
    msp.add_text("32950", height=260, dxfattribs={'layer': 'DIMENSIONS'}).set_placement((32950/2.0, -ext - 1580), align=TextEntityAlignment.CENTER)

    # 3. Dầm
    for b in beams:
        p1 = b["p1"]
        p2 = b["p2"]
        x1, y1 = p1[0], p1[1]
        x2, y2 = p2[0], p2[1]

        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx*dx + dy*dy)
        if length < 1:
            continue

        bw = b.get("width", 200.0)
        hw = bw / 2.0
        nx = -dy / length
        ny = dx / length

        v1 = (x1 - hw * nx, y1 - hw * ny)
        v2 = (x1 + hw * nx, y1 + hw * ny)
        v3 = (x2 + hw * nx, y2 + hw * ny)
        v4 = (x2 - hw * nx, y2 - hw * ny)

        msp.add_lwpolyline([v1, v2, v3, v4, v1], dxfattribs={'layer': 'BEAM_OUTLINE'})
        msp.add_line((x1, y1), (x2, y2), dxfattribs={'layer': 'BEAM_CENTERLINE', 'linetype': 'DASHED'})

        # Text ký hiệu dầm
        mid_x = (x1 + x2) / 2.0
        mid_y = (y1 + y2) / 2.0
        l_id = b.get("long_beam_id") or b.get("label", "B")
        sec_str = b.get("section", "200x400").replace("B ", "")
        lbl_text = f"{l_id} ({sec_str})"

        rot = 90 if abs(dy) > abs(dx) else 0
        t = msp.add_text(lbl_text, height=180, dxfattribs={'layer': 'BEAM_TEXT', 'rotation': rot})
        t.set_placement((mid_x, mid_y), align=TextEntityAlignment.CENTER)

    # 4. Cột
    for col in columns:
        p1 = col["p1"]
        cx, cy = p1[0], p1[1]
        cw = col.get("width", 300.0)
        cd = col.get("depth", 300.0)
        cp1 = (cx - cw/2.0, cy - cd/2.0)
        cp2 = (cx + cw/2.0, cy - cd/2.0)
        cp3 = (cx + cw/2.0, cy + cd/2.0)
        cp4 = (cx - cw/2.0, cy + cd/2.0)

        msp.add_lwpolyline([cp1, cp2, cp3, cp4, cp1], dxfattribs={'layer': 'COLUMN_CONCRETE'})

    # 5. Tiêu đề
    title_info = STORY_TITLES.get(story, (f"MẶT BẰNG KÝ HIỆU DẦM ({story})", "+0.000"))
    msp.add_text(f"{title_info[0]} • CAO ĐỘ {title_info[1]}", height=650, dxfattribs={'layer': 'TITLE_TEXT'}).set_placement((16475, 14800), align=TextEntityAlignment.CENTER)
    msp.add_text("DỰ ÁN: CẢI TẠO PHƯƠNG ÁN B • TIÊU CHUẨN: TCVN 5574:2018 • TỶ LỆ 1:100", height=300, dxfattribs={'layer': 'TITLE_TEXT'}).set_placement((16475, 13900), align=TextEntityAlignment.CENTER)

    if output_path:
        doc.saveas(output_path)
        return output_path

    stream = io.StringIO()
    doc.write(stream)
    return stream.getvalue().encode('utf-8')


if __name__ == '__main__':
    for st in ['DK', 'T3', 'T4']:
        pdf = f"test_beam_plan_{st}.pdf"
        dxf = f"test_beam_plan_{st}.dxf"
        generate_beam_plan_pdf(output_path=pdf, story=st)
        generate_beam_plan_dxf(output_path=dxf, story=st)
        print(f"Generated {st}: PDF={os.path.getsize(pdf)} bytes, DXF={os.path.getsize(dxf)} bytes")
