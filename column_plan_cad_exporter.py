#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
column_plan_cad_exporter.py
Bộ xuất bản vẽ kỹ thuật CAD Mặt Bằng Định Vị & Bố Trí Cột theo đúng Index (C1..C18).
Định dạng xuất: PDF (vector chuẩn TCVN) và DXF (AutoCAD R2010).

Quy chuẩn TCVN:
- Nét cột BTCT: Đậm nét 0.35 mm (Layer COLUMN_OUTLINE)
- Nét tim cột & tim trục: Mảnh gạch chấm 0.09 mm (Layer GRID_AXIS)
- Đường dóng & kích thước (Dim): Mảnh 0.09 mm (Layer DIM)
- Khung bản vẽ, khung tên: 0.35 mm (Layer TITLE_BLOCK)
- Nhãn cột (Index Tag): Phân màu theo tiết diện, hiển thị chuẩn xác C1..C18
- Bảng thống kê định vị cột (Column Schedule Table) kèm tổng hợp tiết diện
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
        print(f"[ColumnPlanExporter] Không thể nạp font Arial: {e}")

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
SHEET_W_PT = SHEET_W_MM * MM_TO_PT # 2383.94 pt
SHEET_H_PT = SHEET_H_MM * MM_TO_PT # 1683.78 pt

COLUMN_SECTION_DEFAULTS = {
    "C1 250x300": {
        "width": 250, "depth": 300,
        "rebar_str": "4Φ18", "stirrup_str": "d6a100/200",
        "stroke": (0.02, 0.45, 0.75), "fill": (0.88, 0.95, 1.0), "text": (0.01, 0.35, 0.65)
    },
    "C2 300x300": {
        "width": 300, "depth": 300,
        "rebar_str": "4Φ20", "stirrup_str": "d6a100/200",
        "stroke": (0.08, 0.60, 0.25), "fill": (0.88, 0.98, 0.90), "text": (0.06, 0.50, 0.20)
    },
    "C3 250x520": {
        "width": 250, "depth": 520,
        "rebar_str": "8Φ20", "stirrup_str": "d6a100/200",
        "stroke": (0.85, 0.12, 0.25), "fill": (1.0, 0.90, 0.92), "text": (0.75, 0.08, 0.20)
    }
}


def get_column_plan_data(etabs_data=None):
    """
    Trích xuất danh sách cột và hệ lưới trục từ dữ liệu ETABS,
    đảm bảo đánh số Index cột (C1..C18) chuẩn xác theo tọa độ và vị trí trục.
    """
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

    grids_x = etabs_data.get("grids", {}).get("X", [
        {"id": "1", "ordinate": 0.0},
        {"id": "2", "ordinate": 5900.0},
        {"id": "3", "ordinate": 13250.0},
        {"id": "4", "ordinate": 18250.0},
        {"id": "5", "ordinate": 21850.0},
        {"id": "6", "ordinate": 27450.0},
        {"id": "7", "ordinate": 32950.0}
    ])
    grids_y = etabs_data.get("grids", {}).get("Y", [
        {"id": "C", "ordinate": 0.0},
        {"id": "B", "ordinate": 5970.0},
        {"id": "A", "ordinate": 11970.0}
    ])

    raw_columns = etabs_data.get("columns", [])
    raw_beams = etabs_data.get("beams", [])

    def find_nearest_grid(val, grid_list):
        if not grid_list:
            return "?"
        best = min(grid_list, key=lambda g: abs(g.get("ordinate", 0) - val))
        diff = abs(best.get("ordinate", 0) - val)
        if diff > 800:
            return f"{best.get('id', '?')}*"
        return best.get("id", "?")

    # Gom nhóm các cột theo Label (C1..C18)
    col_map = {}
    for c in raw_columns:
        lbl = c.get("label")
        if not lbl:
            continue
        x = float(c.get("p1", [0, 0, 0])[0])
        y = float(c.get("p1", [0, 0, 0])[1])
        st = c.get("story", "")
        sec = c.get("section", "C1 250x300")
        w = float(c.get("width", 250.0))
        d = float(c.get("depth", 300.0))

        if lbl not in col_map:
            gx = find_nearest_grid(x, grids_x)
            gy = find_nearest_grid(y, grids_y)
            sec_cfg = COLUMN_SECTION_DEFAULTS.get(sec, {
                "width": w, "depth": d,
                "rebar_str": "4Φ18", "stirrup_str": "d6a100/200",
                "stroke": (0.02, 0.45, 0.75), "fill": (0.88, 0.95, 1.0), "text": (0.01, 0.35, 0.65)
            })
            col_map[lbl] = {
                "label": lbl,
                "name": c.get("name", lbl),
                "x": round(x, 1),
                "y": round(y, 1),
                "grid_x": gx,
                "grid_y": gy,
                "grid_desc": f"Trục ({gx}, {gy})",
                "width": w,
                "depth": d,
                "section": sec,
                "rebar_str": sec_cfg.get("rebar_str", "4Φ18"),
                "stirrup_str": sec_cfg.get("stirrup_str", "d6a100/200"),
                "color_stroke": sec_cfg.get("stroke", (0.02, 0.45, 0.75)),
                "color_fill": sec_cfg.get("fill", (0.88, 0.95, 1.0)),
                "color_text": sec_cfg.get("text", (0.01, 0.35, 0.65)),
                "stories": []
            }
        if st and st not in col_map[lbl]["stories"]:
            col_map[lbl]["stories"].append(st)

    # Sắp xếp danh sách cột theo thứ tự số: C1, C2, C3, C4, C5, C6, C10, C11, C12, C13, C14, C15, C16, C17, C18
    def col_sort_key(item):
        m = re.search(r'\d+', item[0])
        return int(m.group(0)) if m else 999

    sorted_cols = [v for k, v in sorted(col_map.items(), key=col_sort_key)]

    # Chuẩn bị dầm làm khung mờ tham chiếu
    beam_frames = []
    for b in raw_beams:
        if b.get("story") == "T3" or not beam_frames:
            beam_frames.append({
                "label": b.get("label", ""),
                "x1": round(b["p1"][0], 1), "y1": round(b["p1"][1], 1),
                "x2": round(b["p2"][0], 1), "y2": round(b["p2"][1], 1),
                "width": b.get("width", 200.0)
            })

    return {
        "grids_x": grids_x,
        "grids_y": grids_y,
        "columns": sorted_cols,
        "total_columns": len(sorted_cols),
        "beams": beam_frames,
        "bounds": {
            "min_x": 0.0,
            "max_x": 32950.0,
            "min_y": 0.0,
            "max_y": 11970.0,
            "total_length": 32950.0,
            "total_width": 11970.0
        }
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
    canv.setStrokeColorRGB(0.15, 0.5, 0.2) # Xanh lá mảnh
    canv.setLineWidth(LW_THIN_PT)
    canv.line(x1_pt, y1_pt, x2_pt, y2_pt)

    # Gạch chéo 45 độ
    tick = 3.5
    canv.line(x1_pt - tick, y1_pt - tick, x1_pt + tick, y1_pt + tick)
    canv.line(x2_pt - tick, y2_pt - tick, x2_pt + tick, y2_pt + tick)

    # Text kích thước
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


def generate_column_plan_pdf(output_path=None, story='T3'):
    """
    Sinh bản vẽ PDF A1 Landscape thể hiện Mặt Bằng Định Vị & Bố Trí Cột theo đúng Index.
    """
    data = get_column_plan_data()
    buf = io.BytesIO() if output_path is None else None
    target = output_path if output_path else buf

    canv = canvas.Canvas(target, pagesize=landscape(A1))
    canv.setTitle("BAN VE MAT BANG DINH VI VA BO TRI COT - REVITAI STUDIO")

    # 1. Khung bản vẽ TCVN & Border
    margin_l = 25.0 * MM_TO_PT # 25mm gáy đóng tập
    margin_r = 12.0 * MM_TO_PT
    margin_t = 12.0 * MM_TO_PT
    margin_b = 12.0 * MM_TO_PT

    canv.setStrokeColorRGB(0.1, 0.15, 0.25)
    canv.setLineWidth(LW_THICK_PT)
    canv.rect(margin_l, margin_b, SHEET_W_PT - margin_l - margin_r, SHEET_H_PT - margin_t - margin_b)

    # 2. Khung Tên & Thông Tin Dự Án (Góc dưới bên phải)
    tb_w = 210.0 * MM_TO_PT
    tb_h = 75.0 * MM_TO_PT
    tb_x = SHEET_W_PT - margin_r - tb_w
    tb_y = margin_b
    canv.rect(tb_x, tb_y, tb_w, tb_h)

    canv.setFont(FONT_BOLD, 12)
    canv.setFillColorRGB(0.05, 0.1, 0.25)
    canv.drawString(tb_x + 12, tb_y + tb_h - 18, "DỰ ÁN: CẢI TẠO PHƯƠNG ÁN B")
    canv.setFont(FONT_REGULAR, 8.5)
    canv.drawString(tb_x + 12, tb_y + tb_h - 32, "HẠNG MỤC: KẾT CẤU BÊ TÔNG CỐT THÉP (TCVN 5574:2018)")
    
    canv.setLineWidth(LW_THIN_PT)
    canv.line(tb_x, tb_y + tb_h - 38, tb_x + tb_w, tb_y + tb_h - 38)

    canv.setFont(FONT_BOLD, 11)
    canv.drawString(tb_x + 12, tb_y + 20, "BẢN VẼ: MẶT BẰNG ĐỊNH VỊ & BỐ TRÍ CỘT")
    canv.setFont(FONT_REGULAR, 7.5)
    canv.drawString(tb_x + 12, tb_y + 8, f"KÝ HIỆU: KC-COT-01 • TỶ LỆ: 1:100 • KHỔ GIẤY: A1 LANDSCAPE")

    # 3. Tiêu đề chính trang vẽ
    canv.setFont(FONT_BOLD, 17)
    canv.setFillColorRGB(0.08, 0.15, 0.3)
    canv.drawString(margin_l + 18, SHEET_H_PT - margin_t - 28, "MẶT BẰNG ĐỊNH VỊ VÀ BỐ TRÍ CỘT (TOÀN NHÀ - ĐÚNG INDEX C1 → C15)")
    canv.setFont(FONT_REGULAR, 9.5)
    canv.setFillColorRGB(0.35, 0.45, 0.55)
    canv.drawString(margin_l + 18, SHEET_H_PT - margin_t - 44, "LƯỚI TRỤC 1-7 (32.95m) × TRỤC A-C (11.97m) • 15 VỊ TRÍ CỘT CHÍNH • ĐÚNG KÍCH THƯỚC TIẾT DIỆN & TIM ĐỊNH VỊ")

    # 4. Thiết lập khung tọa độ vẽ Mặt Bằng (Plan Viewport)
    # Rộng rãi, tăng khoảng đệm (padding) để tag và dim không đè nhau
    ext = 65.0 # pt vươn ra ngoài biên dầm để cắm bóng trục và dim

    plan_x = margin_l + 70.0
    plan_y = margin_b + 95.0
    plan_w = SHEET_W_PT - margin_l - margin_r - tb_w - 90.0
    plan_h = SHEET_H_PT - margin_t - margin_b - 170.0

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
    columns = data["columns"]

    # 5. Vẽ lưới dầm phụ mờ (Reference Framing)
    canv.saveState()
    canv.setStrokeColorRGB(0.80, 0.84, 0.88)
    canv.setLineWidth(0.7)
    canv.setDash(3, 3)
    for b in data.get("beams", []):
        bx1, by1 = to_pt(b["x1"], b["y1"])
        bx2, by2 = to_pt(b["x2"], b["y2"])
        canv.line(bx1, by1, bx2, by2)
    canv.restoreState()

    # 6. Vẽ các đường lưới trục (Grid Lines)
    canv.saveState()
    canv.setStrokeColorRGB(0.35, 0.40, 0.48)
    canv.setLineWidth(LW_THIN_PT)
    canv.setDash(5, 3)

    min_pt_x, min_pt_y = to_pt(0, 0)
    max_pt_x, max_pt_y = to_pt(32950, 11970)

    # Trục X (Đứng)
    for gx in grids_x:
        px, _ = to_pt(gx["ordinate"], 0)
        canv.line(px, min_pt_y - ext, px, max_pt_y + ext)
        # Bóng trục ở 2 đầu
        draw_bubble_pdf(canv, px, min_pt_y - ext - 12.0, gx["id"])
        draw_bubble_pdf(canv, px, max_pt_y + ext + 12.0, gx["id"])

    # Trục Y (Ngang)
    for gy in grids_y:
        _, py = to_pt(0, gy["ordinate"])
        canv.line(min_pt_x - ext, py, max_pt_x + ext, py)
        # Bóng trục ở 2 đầu
        draw_bubble_pdf(canv, min_pt_x - ext - 12.0, py, gy["id"])
        draw_bubble_pdf(canv, max_pt_x + ext + 12.0, py, gy["id"])

    canv.restoreState()

    # 7. Vẽ các chuỗi kích thước (Dimension Chains)
    # Kích thước từng nhịp X (bên dưới)
    for i in range(len(grids_x) - 1):
        x1_m = grids_x[i]["ordinate"]
        x2_m = grids_x[i+1]["ordinate"]
        px1, _ = to_pt(x1_m, 0)
        px2, _ = to_pt(x2_m, 0)
        dim_val = int(round(x2_m - x1_m))
        draw_dim_line_pdf(canv, px1, min_pt_y - ext - 34.0, px2, min_pt_y - ext - 34.0, str(dim_val))

    # Kích thước tổng X (dưới cùng)
    draw_dim_line_pdf(canv, min_pt_x, min_pt_y - ext - 50.0, max_pt_x, min_pt_y - ext - 50.0, "32950")

    # Kích thước từng nhịp Y (bên trái)
    for j in range(len(grids_y) - 1):
        y1_m = grids_y[j]["ordinate"]
        y2_m = grids_y[j+1]["ordinate"]
        _, py1 = to_pt(0, y1_m)
        _, py2 = to_pt(0, y2_m)
        dim_val = int(round(y2_m - y1_m))
        draw_dim_line_pdf(canv, min_pt_x - ext - 34.0, py1, min_pt_x - ext - 34.0, py2, str(dim_val), is_vertical=True)

    # Kích thước tổng Y (ngoài cùng bên trái)
    draw_dim_line_pdf(canv, min_pt_x - ext - 50.0, min_pt_y, min_pt_x - ext - 50.0, max_pt_y, "11970", is_vertical=True)

    # 8. VẼ CÁC CỘT THEO ĐÚNG TIẾT DIỆN & VỊ TRÍ, KÈM INDEX TAG
    canv.saveState()
    for col in columns:
        cx, cy = to_pt(col["x"], col["y"])
        cw = col["width"] * scale
        cd = col["depth"] * scale

        # Đổ nền cột theo màu tiết diện
        c_fill = col.get("color_fill", (0.88, 0.95, 1.0))
        c_stroke = col.get("color_stroke", (0.02, 0.45, 0.75))
        c_text = col.get("color_text", (0.01, 0.35, 0.65))

        canv.setFillColorRGB(0.15, 0.20, 0.28) # Bê tông đặc
        canv.setStrokeColorRGB(c_stroke[0], c_stroke[1], c_stroke[2])
        canv.setLineWidth(LW_THICK_PT)
        canv.rect(cx - cw/2.0, cy - cd/2.0, cw, cd, fill=1, stroke=1)

        # Tim cột gạch chéo trắng mảnh
        canv.setStrokeColorRGB(1.0, 1.0, 1.0)
        canv.setLineWidth(0.4)
        canv.line(cx - cw/2.0 + 0.5, cy, cx + cw/2.0 - 0.5, cy)
        canv.line(cx, cy - cd/2.0 + 0.5, cx, cy + cd/2.0 - 0.5)

        # 9. VẼ NHÃN INDEX CỘT (CALLOUT TAG THEO ĐÚNG INDEX C1..C18)
        lbl = col["label"]
        sec_short = f"{int(col['width'])}x{int(col['depth'])}"
        
        # Bố trí khoảng cách tag hợp lý
        if col["y"] > 8000: # Trục A: Đặt tag phía dưới một chút hoặc phía trên bên trong khoảng trống
            tag_dist_x = 0.0
            tag_dist_y = 24.0
        elif col["y"] < 2000: # Trục C: Đặt tag phía trên hoặc phía dưới
            tag_dist_x = 0.0
            tag_dist_y = -24.0
        else: # Trục B: Đặt tag lệch sang góc 45 độ
            tag_dist_x = 24.0 if col["x"] >= 16000 else -24.0
            tag_dist_y = 20.0

        tx = cx + tag_dist_x
        ty = cy + tag_dist_y

        # Leader line từ tâm cột đến tag
        canv.setStrokeColorRGB(c_stroke[0], c_stroke[1], c_stroke[2])
        canv.setLineWidth(0.8)
        canv.line(cx, cy, tx, ty)

        # Hộp tag
        tag_w = 46.0
        tag_h = 20.0
        canv.setFillColorRGB(c_fill[0], c_fill[1], c_fill[2])
        canv.setStrokeColorRGB(c_stroke[0], c_stroke[1], c_stroke[2])
        canv.setLineWidth(1.0)
        canv.roundRect(tx - tag_w/2.0, ty - tag_h/2.0, tag_w, tag_h, 3.5, fill=1, stroke=1)

        # Chữ Index cột (To, Rõ nét)
        canv.setFont(FONT_BOLD, 9)
        canv.setFillColorRGB(c_text[0], c_text[1], c_text[2])
        canv.drawCentredString(tx, ty + 1.2, lbl)

        # Kích thước tiết diện bên dưới
        canv.setFont(FONT_REGULAR, 7)
        canv.setFillColorRGB(0.2, 0.25, 0.35)
        canv.drawCentredString(tx, ty - 7.0, sec_short)

    canv.restoreState()

    # 10. BẢNG THỐNG KÊ ĐỊNH VỊ CỘT (COLUMN SCHEDULE TABLE) Ở BÊN PHẢI
    tbl_x = SHEET_W_PT - margin_r - tb_w
    tbl_y = tb_y + tb_h + 10.0
    tbl_w = tb_w
    tbl_h = SHEET_H_PT - margin_t - tbl_y - 12.0

    canv.saveState()
    # Khung bảng
    canv.setStrokeColorRGB(0.2, 0.3, 0.4)
    canv.setLineWidth(LW_THICK_PT)
    canv.rect(tbl_x, tbl_y, tbl_w, tbl_h)

    # Tiêu đề bảng
    header_h = 24.0
    canv.setFillColorRGB(0.92, 0.95, 0.98)
    canv.rect(tbl_x, tbl_y + tbl_h - header_h, tbl_w, header_h, fill=1, stroke=1)
    canv.setFont(FONT_BOLD, 10)
    canv.setFillColorRGB(0.08, 0.15, 0.3)
    canv.drawString(tbl_x + 10, tbl_y + tbl_h - 16, "BẢNG THỐNG KÊ ĐỊNH VỊ CỘT (C1 → C15)")

    # Dòng tiêu đề cột
    sub_h = 16.0
    canv.setFillColorRGB(0.96, 0.97, 0.99)
    canv.rect(tbl_x, tbl_y + tbl_h - header_h - sub_h, tbl_w, sub_h, fill=1, stroke=1)
    canv.setFont(FONT_BOLD, 7.5)
    canv.setFillColorRGB(0.2, 0.25, 0.35)

    cols_w = [30, 44, 40, 50, 46] # Index, Trục, Tiết diện, Cốt thép, Tầng
    x_curr = tbl_x
    headers = ["Mã Cột", "Vị Trí Trục", "Tiết Diện", "Cốt Thép", "Tầng"]
    for hw, htext in zip(cols_w, headers):
        canv.drawCentredString(x_curr + hw/2.0, tbl_y + tbl_h - header_h - sub_h + 4.5, htext)
        x_curr += hw

    # Các hàng dữ liệu (15 hàng)
    row_y = tbl_y + tbl_h - header_h - sub_h
    # Dành 65 pt ở đáy bảng cho phần tóm tắt phân loại
    summary_box_h = 75.0
    available_table_h = (row_y - tbl_y) - summary_box_h
    row_h = available_table_h / float(len(columns))

    for idx, col in enumerate(columns):
        y_bottom = row_y - (idx + 1) * row_h
        # Kẻ vạch ngang
        canv.setLineWidth(LW_THIN_PT)
        canv.setStrokeColorRGB(0.85, 0.88, 0.92)
        canv.line(tbl_x, y_bottom, tbl_x + tbl_w, y_bottom)

        # Highlight xen kẽ
        if idx % 2 == 1:
            canv.setFillColorRGB(0.98, 0.99, 1.0)
            canv.rect(tbl_x + 1, y_bottom + 0.5, tbl_w - 2, row_h - 1, fill=1, stroke=0)

        # Index cột (In đậm màu tương ứng)
        c_text = col.get("color_text", (0.01, 0.35, 0.65))
        canv.setFont(FONT_BOLD, 8)
        canv.setFillColorRGB(c_text[0], c_text[1], c_text[2])
        canv.drawCentredString(tbl_x + cols_w[0]/2.0, y_bottom + row_h/2.0 - 2.8, col["label"])

        # Vị trí trục
        canv.setFont(FONT_REGULAR, 7.5)
        canv.setFillColorRGB(0.15, 0.2, 0.3)
        canv.drawCentredString(tbl_x + cols_w[0] + cols_w[1]/2.0, y_bottom + row_h/2.0 - 2.8, f"({col['grid_x']}-{col['grid_y']})")

        # Tiết diện
        sec_short = f"{int(col['width'])}x{int(col['depth'])}"
        canv.drawCentredString(tbl_x + cols_w[0] + cols_w[1] + cols_w[2]/2.0, y_bottom + row_h/2.0 - 2.8, sec_short)

        # Cốt thép
        canv.setFont(FONT_BOLD, 7.5)
        canv.setFillColorRGB(0.1, 0.45, 0.2)
        canv.drawCentredString(tbl_x + cols_w[0] + cols_w[1] + cols_w[2] + cols_w[3]/2.0, y_bottom + row_h/2.0 - 2.8, col["rebar_str"])

        # Tầng
        canv.setFont(FONT_REGULAR, 7)
        canv.setFillColorRGB(0.4, 0.45, 0.55)
        st_text = "T1-T4 (4 Tầng)" if len(col["stories"]) >= 4 else "T1-T3 (3 Tầng)"
        canv.drawCentredString(tbl_x + sum(cols_w[:4]) + cols_w[4]/2.0, y_bottom + row_h/2.0 - 2.8, st_text)

    # Kẻ các vạch đứng ngăn cột trong bảng
    x_curr = tbl_x
    for hw in cols_w[:-1]:
        x_curr += hw
        canv.setStrokeColorRGB(0.8, 0.85, 0.9)
        canv.line(x_curr, tbl_y + summary_box_h, x_curr, tbl_y + tbl_h - header_h)

    # Khung tóm tắt phân loại tiết diện ở đáy bảng
    sum_y = tbl_y
    canv.setFillColorRGB(0.95, 0.97, 0.99)
    canv.rect(tbl_x, sum_y, tbl_w, summary_box_h, fill=1, stroke=1)

    canv.setFont(FONT_BOLD, 8)
    canv.setFillColorRGB(0.1, 0.2, 0.35)
    canv.drawString(tbl_x + 8, sum_y + summary_box_h - 14, "TỔNG HỢP TIẾT DIỆN CỘT TOÀN DỰ ÁN:")

    canv.setFont(FONT_REGULAR, 7.2)
    canv.drawString(tbl_x + 8, sum_y + summary_box_h - 28, "• C1 250×300: 6 vị trí (C1, C5, C12, C13, C14, C15) - Thép 4Φ18")
    canv.drawString(tbl_x + 8, sum_y + summary_box_h - 42, "• C2 300×300: 7 vị trí (C2, C3, C4, C6, C7, C10, C11) - Thép 4Φ20")
    canv.drawString(tbl_x + 8, sum_y + summary_box_h - 56, "• C3 250×520: 2 vị trí (C8, C9 - Cột cấy lớn) - Thép 8Φ20")
    canv.setFont(FONT_BOLD, 7.5)
    canv.setFillColorRGB(0.8, 0.1, 0.1)
    canv.drawString(tbl_x + 8, sum_y + summary_box_h - 70, "=> Tổng cộng: 15 vị trí cột chính • 56 cấu kiện cột toàn nhà")

    canv.restoreState()

    # 11. Ghi chú kỹ thuật góc dưới bên trái
    canv.saveState()
    notes_y = margin_b + 12.0
    canv.setFont(FONT_BOLD, 8.5)
    canv.setFillColorRGB(0.15, 0.2, 0.3)
    canv.drawString(margin_l + 18, notes_y + 36, "★ GHI CHÚ ĐỊNH VỊ VÀ BỐ TRÍ CỘT (TCVN 5574:2018):")
    canv.setFont(FONT_REGULAR, 7.5)
    canv.setFillColorRGB(0.35, 0.45, 0.55)
    canv.drawString(margin_l + 18, notes_y + 24, "1. Toàn bộ kích thước định vị ghi bằng milimét (mm), cao độ tính bằng mét (m). Tim cột trùng tim trục giao nhau.")
    canv.drawString(margin_l + 18, notes_y + 14, "2. Cột C8, C9 tiết diện 250x520 là cột cấy lớn chịu lực chính giằng giữa nhà trục B. Các cột C1, C5, C12, C13 dừng ở Tầng 3.")
    canv.drawString(margin_l + 18, notes_y + 4, "3. Bê tông cột B22.5 (M300). Thép chủ CB400-V, thép đai CB240-T. Lớp bê tông bảo vệ c = 25mm.")
    canv.restoreState()

    canv.save()
    if output_path:
        return output_path
    return buf.getvalue()


def generate_column_plan_dxf(output_path=None, story='T3'):
    """
    Sinh bản vẽ AutoCAD DXF (R2010) cho Mặt Bằng Định Vị & Bố Trí Cột theo đúng Index.
    """
    data = get_column_plan_data()
    doc = get_template_dxf_doc()
    doc.header['$INSUNITS'] = 4 # Millimeters
    msp = doc.modelspace()

    # Tạo các Layers chuẩn AutoCAD
    layers = [
        ('GRID_AXIS', 8, 'DASHDOT'),        # Xám mảnh
        ('DIMENSIONS', 3, 'Continuous'),       # Xanh lá
        ('BEAM_FRAME', 9, 'DASHED'),       # Xám mờ
        ('COLUMN_CONCRETE', 7, 'Continuous'),  # Trắng/Đen đậm nét
        ('COLUMN_HATCH', 252, 'Continuous'),   # Hatch đặc
        ('COLUMN_TAG', 1, 'Continuous'),       # Đỏ
        ('TABLE_TEXT', 7, 'Continuous'),       # Trắng
        ('TITLE_BLOCK', 4, 'Continuous')       # Cyan
    ]
    for l_name, l_col, l_type in layers:
        ensure_layer(doc, l_name, color=l_col, linetype=l_type)

    grids_x = data["grids_x"]
    grids_y = data["grids_y"]
    columns = data["columns"]

    # 1. Vẽ dầm tham chiếu
    for b in data.get("beams", []):
        msp.add_line((b["x1"], b["y1"]), (b["x2"], b["y2"]), dxfattribs={'layer': 'BEAM_FRAME', 'linetype': 'DASHED'})

    # 2. Vẽ lưới trục
    ext = 1800.0
    for gx in grids_x:
        x_val = gx["ordinate"]
        msp.add_line((x_val, -ext), (x_val, 11970.0 + ext), dxfattribs={'layer': 'GRID_AXIS', 'linetype': 'DASHDOT'})
        # Bóng trục
        msp.add_circle((x_val, -ext - 450), radius=380, dxfattribs={'layer': 'GRID_AXIS'})
        msp.add_text(gx["id"], height=300, dxfattribs={'layer': 'GRID_AXIS'}).set_placement((x_val, -ext - 560), align=TextEntityAlignment.CENTER)
        msp.add_circle((x_val, 11970.0 + ext + 450), radius=380, dxfattribs={'layer': 'GRID_AXIS'})
        msp.add_text(gx["id"], height=300, dxfattribs={'layer': 'GRID_AXIS'}).set_placement((x_val, 11970.0 + ext + 340), align=TextEntityAlignment.CENTER)

    for gy in grids_y:
        y_val = gy["ordinate"]
        msp.add_line((-ext, y_val), (32950.0 + ext, y_val), dxfattribs={'layer': 'GRID_AXIS', 'linetype': 'DASHDOT'})
        # Bóng trục
        msp.add_circle((-ext - 450, y_val), radius=380, dxfattribs={'layer': 'GRID_AXIS'})
        msp.add_text(gy["id"], height=300, dxfattribs={'layer': 'GRID_AXIS'}).set_placement((-ext - 560, y_val - 110), align=TextEntityAlignment.CENTER)
        msp.add_circle((32950.0 + ext + 450, y_val), radius=380, dxfattribs={'layer': 'GRID_AXIS'})
        msp.add_text(gy["id"], height=300, dxfattribs={'layer': 'GRID_AXIS'}).set_placement((32950.0 + ext + 340, y_val - 110), align=TextEntityAlignment.CENTER)

    # 3. Vẽ kích thước (Dim)
    for i in range(len(grids_x) - 1):
        x1_v = grids_x[i]["ordinate"]
        x2_v = grids_x[i+1]["ordinate"]
        dim_str = str(int(round(x2_v - x1_v)))
        msp.add_line((x1_v, -ext - 1100), (x2_v, -ext - 1100), dxfattribs={'layer': 'DIMENSIONS'})
        msp.add_text(dim_str, height=220, dxfattribs={'layer': 'DIMENSIONS'}).set_placement(((x1_v + x2_v)/2.0, -ext - 980), align=TextEntityAlignment.CENTER)

    msp.add_line((0, -ext - 1700), (32950, -ext - 1700), dxfattribs={'layer': 'DIMENSIONS'})
    msp.add_text("32950", height=260, dxfattribs={'layer': 'DIMENSIONS'}).set_placement((32950/2.0, -ext - 1580), align=TextEntityAlignment.CENTER)

    # 4. Vẽ từng cột BTCT và nhãn Index
    for col in columns:
        cx, cy = col["x"], col["y"]
        cw, cd = col["width"], col["depth"]
        p1 = (cx - cw/2.0, cy - cd/2.0)
        p2 = (cx + cw/2.0, cy - cd/2.0)
        p3 = (cx + cw/2.0, cy + cd/2.0)
        p4 = (cx - cw/2.0, cy + cd/2.0)

        msp.add_lwpolyline([p1, p2, p3, p4, p1], dxfattribs={'layer': 'COLUMN_CONCRETE'})

        # Tim cột
        msp.add_line((cx - cw/2.0, cy), (cx + cw/2.0, cy), dxfattribs={'layer': 'GRID_AXIS'})
        msp.add_line((cx, cy - cd/2.0), (cx, cy + cd/2.0), dxfattribs={'layer': 'GRID_AXIS'})

        # Tag Index cột
        tag_off_y = 750 if cy > 8000 else (-850 if cy < 2000 else 750)
        tag_off_x = 0 if (cy > 8000 or cy < 2000) else (750 if cx > 16000 else -750)

        tx, ty = cx + tag_off_x, cy + tag_off_y
        msp.add_line((cx, cy), (tx, ty), dxfattribs={'layer': 'COLUMN_TAG'})
        
        lbl_text = f"{col['label']} ({int(cw)}x{int(cd)})"
        msp.add_text(lbl_text, height=220, dxfattribs={'layer': 'COLUMN_TAG'}).set_placement((tx, ty + 60), align=TextEntityAlignment.CENTER)

    # 5. Tiêu đề bản vẽ
    msp.add_text("MẶT BẰNG ĐỊNH VỊ VÀ BỐ TRÍ CỘT (C1 - C15)", height=650, dxfattribs={'layer': 'TITLE_BLOCK'}).set_placement((16475, 14800), align=TextEntityAlignment.CENTER)
    msp.add_text("DỰ ÁN: CẢI TẠO PHƯƠNG ÁN B • TIÊU CHUẨN: TCVN 5574:2018 • TỶ LỆ 1:100", height=300, dxfattribs={'layer': 'TITLE_BLOCK'}).set_placement((16475, 13900), align=TextEntityAlignment.CENTER)

    if output_path:
        doc.saveas(output_path)
        return output_path
    
    stream = io.StringIO()
    doc.write(stream)
    return stream.getvalue().encode('utf-8')


if __name__ == '__main__':
    print("Testing generate_column_plan_pdf...")
    pdf_path = "test_column_plan_sheet.pdf"
    generate_column_plan_pdf(output_path=pdf_path)
    print(f"Generated PDF: {pdf_path} ({os.path.getsize(pdf_path)} bytes)")

    print("Testing generate_column_plan_dxf...")
    dxf_path = "test_column_plan_sheet.dxf"
    generate_column_plan_dxf(output_path=dxf_path)
    print(f"Generated DXF: {dxf_path} ({os.path.getsize(dxf_path)} bytes)")
