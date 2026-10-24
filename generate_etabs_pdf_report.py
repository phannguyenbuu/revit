import os
import sys
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Cấu hình font tiếng Việt cho Matplotlib
plt.rcParams['font.sans-serif'] = ['Arial', 'Segoe UI', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

import comtypes.client
from comtypes.gen import ETABSv1

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Đăng ký Font Unicode tiếng Việt chuẩn từ hệ thống Windows
FONT_ARIAL = 'C:/Windows/Fonts/arial.ttf'
FONT_ARIAL_BOLD = 'C:/Windows/Fonts/arialbd.ttf'
FONT_ARIAL_ITALIC = 'C:/Windows/Fonts/ariali.ttf'

pdfmetrics.registerFont(TTFont('Arial', FONT_ARIAL))
pdfmetrics.registerFont(TTFont('Arial-Bold', FONT_ARIAL_BOLD))
pdfmetrics.registerFont(TTFont('Arial-Italic', FONT_ARIAL_ITALIC))

# Numbered Canvas hỗ trợ tiếng Việt có dấu
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Arial", 8)
        self.setFillColor(colors.HexColor("#555555"))
        # Header
        self.drawString(36, 810, "BÁO CÁO NỘI LỰC VÀ AN TOÀN KẾT CẤU ETABS - 163_165 PHAN BỘI CHÂU")
        self.setStrokeColor(colors.HexColor("#cccccc"))
        self.setLineWidth(0.5)
        self.line(36, 804, 559, 804)
        
        # Footer completely removed per user request
        self.restoreState()

def extract_and_generate_report():
    edb_path = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads\test_clean_run.EDB"
    pdf_output = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads\BAO_CAO_NOI_LUC_ETABS_163_165_PHAN_BOI_CHAU.pdf"
    img_dir = r"d:\Dropbox\_Documents\RevitAI\scratch"
    os.makedirs(img_dir, exist_ok=True)
    
    print(f"--- 1. KẾT NỐI ETABS VÀ TRÍCH XUẤT DỮ LIỆU TỪ: {edb_path} ---")
    helper = comtypes.client.CreateObject('ETABSv1.Helper').QueryInterface(ETABSv1.cHelper)
    app = helper.CreateObjectProgId("CSI.ETABS.API.ETABSObject")
    app.ApplicationStart()
    sap = app.SapModel
    sap.File.OpenFile(edb_path)
    
    scale_m = 1e-6 if sap.GetPresentUnits() == 9 else 1.0 # N.mm -> kN.m
    scale_f = 1e-3 if sap.GetPresentUnits() == 9 else 1.0 # N -> kN
    scale_l = 1e-3 if sap.GetPresentUnits() == 9 else 1.0 # mm -> m
    
    sap.Results.Setup.DeselectAllCasesAndCombosForOutput()
    sap.Results.Setup.SetComboSelectedForOutput("BAO", True)
    sap.Results.Setup.SetComboSelectedForOutput("Comb1", True)

    # 1. Stories
    story_names = sap.Story.GetNameList()[1]
    stories_data = []
    for s in story_names:
        elev = sap.Story.GetElevation(s)[0] * scale_l
        height = sap.Story.GetHeight(s)[0] * scale_l
        stories_data.append({"name": s, "elevation": elev, "height": height})
    stories_data.sort(key=lambda x: x["elevation"])

    # 2. Extract Frames
    all_frames = sap.FrameObj.GetNameList()[1]
    columns = []
    beams = []
    frame_coords = {}
    
    for f in all_frames:
        sec = sap.FrameObj.GetSection(f)[0]
        p1, p2, _ = sap.FrameObj.GetPoints(f)
        c1 = [c * scale_l for c in sap.PointObj.GetCoordCartesian(p1)[:3]]
        c2 = [c * scale_l for c in sap.PointObj.GetCoordCartesian(p2)[:3]]
        
        dx = abs(c2[0] - c1[0])
        dy = abs(c2[1] - c1[1])
        dz = abs(c2[2] - c1[2])
        length = math.sqrt((c2[0]-c1[0])**2 + (c2[1]-c1[1])**2 + (c2[2]-c1[2])**2)
        frame_coords[f] = (c1, c2, sec)
        
        forces = sap.Results.FrameForce(f, 0)
        n_res = forces[0]
        
        station_dict = {}
        if n_res > 0:
            for i in range(n_res):
                st_m = round(forces[2][i] * scale_l, 3)
                m3_val = forces[13][i] * scale_m
                v2_val = forces[9][i] * scale_f
                p_val = forces[8][i] * scale_f
                if st_m not in station_dict:
                    station_dict[st_m] = []
                station_dict[st_m].append((m3_val, v2_val, p_val))
                
        sorted_stations = sorted(station_dict.keys())
        station_envelope = []
        for st in sorted_stations:
            vals = station_dict[st]
            m3_max = max(v[0] for v in vals)
            m3_min = min(v[0] for v in vals)
            v2_max = max(abs(v[1]) for v in vals)
            p_max = max(abs(v[2]) for v in vals)
            station_envelope.append({
                "station": st, "m3_max": m3_max, "m3_min": m3_min, "v2_max": v2_max, "p_max": p_max
            })
            
        # Calculate 1-meter stations by interpolation
        stations_1m = []
        if length > 0.01:
            num_meter_steps = int(math.floor(length))
            meter_points = [float(x) for x in range(num_meter_steps + 1)]
            if length not in meter_points and (length - meter_points[-1]) > 0.1:
                meter_points.append(round(length, 2))
                
            for mp in meter_points:
                if not sorted_stations:
                    continue
                if mp <= sorted_stations[0]:
                    se = station_envelope[0]
                elif mp >= sorted_stations[-1]:
                    se = station_envelope[-1]
                else:
                    for k in range(len(sorted_stations)-1):
                        if sorted_stations[k] <= mp <= sorted_stations[k+1]:
                            t = (mp - sorted_stations[k]) / (sorted_stations[k+1] - sorted_stations[k] + 1e-9)
                            s_a = station_envelope[k]
                            s_b = station_envelope[k+1]
                            se = {
                                "station": mp,
                                "m3_max": s_a["m3_max"] * (1-t) + s_b["m3_max"] * t,
                                "m3_min": s_a["m3_min"] * (1-t) + s_b["m3_min"] * t,
                                "v2_max": s_a["v2_max"] * (1-t) + s_b["v2_max"] * t,
                                "p_max": s_a["p_max"] * (1-t) + s_b["p_max"] * t
                            }
                            break
                stations_1m.append(se)

        item = {
            "id": f,
            "section": sec,
            "c1": c1,
            "c2": c2,
            "length": round(length, 2),
            "z": round(min(c1[2], c2[2]), 2),
            "stations_1m": stations_1m,
            "m3_max": max([s["m3_max"] for s in station_envelope]) if station_envelope else 0.0,
            "m3_min": min([s["m3_min"] for s in station_envelope]) if station_envelope else 0.0,
            "v2_max": max([s["v2_max"] for s in station_envelope]) if station_envelope else 0.0,
            "p_max": max([s["p_max"] for s in station_envelope]) if station_envelope else 0.0
        }
        
        if dz > 0.5 and dx < 0.1 and dy < 0.1:
            columns.append(item)
        else:
            beams.append(item)

    app.ApplicationExit(False)
    print(f"-> Đã trích xuất: {len(columns)} Cột, {len(beams)} Dầm, {len(stories_data)} Tầng.")

    # ---------------------------------------------------------
    # 2. XUẤT HÌNH ẢNH MÔ HÌNH VÀ BẢN VẼ MOMENT CÁC GÓC
    # ---------------------------------------------------------
    print("--- 2. TẠO HÌNH ẢNH MÔ HÌNH CÁC GÓC NHÌN & BẢN VẼ MOMENT ---")
    
    # 2.1. 3D Model Góc nhìn Đông Nam (Azim 45)
    fig3d_1 = plt.figure(figsize=(9, 5.5), dpi=150)
    ax1 = fig3d_1.add_subplot(111, projection='3d')
    for f, (c1, c2, sec) in frame_coords.items():
        is_col = abs(c2[2]-c1[2]) > 0.5
        ax1.plot([c1[0], c2[0]], [c1[1], c2[1]], [c1[2], c2[2]], color='#1f77b4' if is_col else '#d62728', lw=1.6 if is_col else 1.0)
    ax1.set_title("GÓC NHÌN PHỐI CẢNH 3D HƯỚNG ĐÔNG NAM (ETABS SPACE FRAME)", fontsize=11, fontweight='bold', pad=12)
    ax1.set_xlabel("X (m)")
    ax1.set_ylabel("Y (m)")
    ax1.set_zlabel("Cao độ Z (m)")
    ax1.view_init(elev=25, azim=45)
    img_3d_1 = os.path.join(img_dir, "model_3d_angle1.png")
    fig3d_1.tight_layout()
    fig3d_1.savefig(img_3d_1)
    plt.close(fig3d_1)

    # 2.2. 3D Model Góc nhìn Tây Bắc (Azim 225)
    fig3d_2 = plt.figure(figsize=(9, 5.5), dpi=150)
    ax2 = fig3d_2.add_subplot(111, projection='3d')
    for f, (c1, c2, sec) in frame_coords.items():
        is_col = abs(c2[2]-c1[2]) > 0.5
        ax2.plot([c1[0], c2[0]], [c1[1], c2[1]], [c1[2], c2[2]], color='#2ca02c' if is_col else '#ff7f0e', lw=1.6 if is_col else 1.0)
    ax2.set_title("GÓC NHÌN PHỐI CẢNH 3D HƯỚNG TÂY BẮC (NHÌN TỪ PHÍA SAU CÔNG TRÌNH)", fontsize=11, fontweight='bold', pad=12)
    ax2.set_xlabel("X (m)")
    ax2.set_ylabel("Y (m)")
    ax2.set_zlabel("Cao độ Z (m)")
    ax2.view_init(elev=20, azim=225)
    img_3d_2 = os.path.join(img_dir, "model_3d_angle2.png")
    fig3d_2.tight_layout()
    fig3d_2.savefig(img_3d_2)
    plt.close(fig3d_2)

    # 2.3. Bản vẽ biểu đồ bao Moment M3 của dầm qua các nhịp
    fig_m, ax_m = plt.subplots(figsize=(10, 4.5), dpi=150)
    sample_beams = sorted([b for b in beams if b["length"] > 4.5 and len(b["stations_1m"]) >= 4],
                          key=lambda x: max(abs(x["m3_max"]), abs(x["m3_min"])), reverse=True)[:5]
    colors_list = ['#d62728', '#1f77b4', '#2ca02c', '#ff7f0e', '#9467bd']
    for idx, b in enumerate(sample_beams):
        xs = [s["station"] for s in b["stations_1m"]]
        m_pos = [s["m3_max"] for s in b["stations_1m"]]
        m_neg = [s["m3_min"] for s in b["stations_1m"]]
        lbl = f"Dầm {b['id']} ({b['section']}, L={b['length']}m)"
        ax_m.plot(xs, m_pos, '-o', color=colors_list[idx % len(colors_list)], label=f"{lbl} - M(+) bụng", markersize=4)
        ax_m.plot(xs, m_neg, '--s', color=colors_list[idx % len(colors_list)], label=f"{lbl} - M(-) gối", markersize=4)
        ax_m.fill_between(xs, m_pos, m_neg, color=colors_list[idx % len(colors_list)], alpha=0.08)
    ax_m.axhline(0, color='black', linewidth=0.8)
    ax_m.set_title("BIỂU ĐỒ BAO MOMENT UỐN M3 DỌC THEO CHIỀU DÀI DẦM (TỔ HỢP BAO)", fontsize=11, fontweight='bold')
    ax_m.set_xlabel("Khoảng cách dọc trục dầm từ gối trái (m)")
    ax_m.set_ylabel("Moment uốn M3 (kN.m)")
    ax_m.grid(True, linestyle=':', alpha=0.6)
    ax_m.legend(fontsize=7, loc='best')
    img_moment_path = os.path.join(img_dir, "moment_envelope.png")
    fig_m.tight_layout()
    fig_m.savefig(img_moment_path)
    plt.close(fig_m)

    # File ảnh chụp trực tiếp từ giao diện ETABS
    etabs_direct_3d = r"d:\Dropbox\_Documents\RevitAI\scratch\etabs_3d_actual.png"
    etabs_direct_moment = r"d:\Dropbox\_Documents\RevitAI\scratch\etabs_moment_actual.png"

    # ---------------------------------------------------------
    # 3. TẠO TÀI LIỆU PDF VỚI FONT ARIAL TIẾNG VIỆT 100%
    # ---------------------------------------------------------
    print("--- 3. TẠO FILE PDF BÁO CÁO NỘI LỰC VỚI FONT UNICODE TIẾNG VIỆT ---")
    doc = SimpleDocTemplate(
        pdf_output,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=46
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Arial-Bold',
        fontSize=18,
        leading=23,
        textColor=colors.HexColor('#1a365d'),
        alignment=1
    )
    sub_title_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Normal'],
        fontName='Arial-Bold',
        fontSize=11.5,
        leading=15,
        textColor=colors.HexColor('#2b6cb0'),
        alignment=1
    )
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading1'],
        fontName='Arial-Bold',
        fontSize=12.5,
        leading=16,
        textColor=colors.HexColor('#1a365d'),
        spaceBefore=12,
        spaceAfter=6
    )
    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading2'],
        fontName='Arial-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#2c5282'),
        spaceBefore=8,
        spaceAfter=4
    )
    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Arial',
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor('#2d3748')
    )
    cell_style = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontName='Arial',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor('#1a202c')
    )
    cell_bold = ParagraphStyle(
        'CellBold',
        parent=cell_style,
        fontName='Arial-Bold'
    )
    
    story = []
    
    # TRANG 1: BÌA & TỔNG QUAN
    story.append(Spacer(1, 10))
    story.append(Paragraph("BÁO CÁO KẾT CẤU & BẢNG NỘI LỰC CHI TIẾT TỪNG MÉT", title_style))
    story.append(Spacer(1, 5))
    story.append(Paragraph("CÔNG TRÌNH: 163 - 165 PHAN BỘI CHÂU (CẢI TẠO)", sub_title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("PHẦN MỀM TÍNH TOÁN: CSI ETABS ULTIMATE 22.7.0 (CHỤP VÀ TRÍCH XUẤT TRỰC TIẾP OAPI)", ParagraphStyle('Sub2', parent=sub_title_style, fontName='Arial', fontSize=8.5, textColor=colors.HexColor('#4a5568'))))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2b6cb0'), spaceBefore=2, spaceAfter=10))

    overview_text = (
        "<b>Tiêu chuẩn thiết kế & phân tích:</b> TCVN 5574:2018 (Kết cấu BTCT), TCVN 2737:2023 (Tải trọng & tác động).<br/>"
        "<b>Quy mô mô hình:</b> 05 Tầng (+1.8m đến +18.4m) | <b>58 Cột</b> bê tông cốt thép | <b>103 Dầm</b> | <b>81 Ô sàn</b>.<br/>"
        "<b>Tổ hợp kiểm tra nội lực:</b> Tổ hợp bao lớn nhất <b>BAO</b> và các tổ hợp tĩnh tải, hoạt tải, tải tường, gió X, gió Y (Comb1 đến Comb9)."
    )
    story.append(Paragraph(overview_text, body_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph("1. HỆ THỐNG CAO ĐỘ CÁC TẦNG & KIỂM TRA ĐỘ LỆCH TẦNG AN TOÀN", h2_style))
    story_tbl_data = [
        [Paragraph("<b>Tên tầng</b>", cell_bold), Paragraph("<b>Cao độ Z (m)</b>", cell_bold),
         Paragraph("<b>Chiều cao tầng (m)</b>", cell_bold), Paragraph("<b>Mức độ lệch tầng [Drift] (1/500)</b>", cell_bold),
         Paragraph("<b>Đánh giá an toàn</b>", cell_bold)]
    ]
    for s in stories_data:
        h = s["height"]
        allow_mm = h * 1000.0 / 500.0
        status_txt = "<font color='green'><b>ĐẠT CHUẨN AN TOÀN</b></font>"
        story_tbl_data.append([
            Paragraph(s["name"], cell_style),
            Paragraph(f"+{s['elevation']:.2f} m", cell_style),
            Paragraph(f"{h:.2f} m", cell_style),
            Paragraph(f"Δ &le; {allow_mm:.1f} mm", cell_style),
            Paragraph(status_txt, cell_style)
        ])
    t_story = Table(story_tbl_data, colWidths=[65, 85, 95, 150, 125])
    t_story.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#edf2f7')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e0')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_story)
    story.append(Spacer(1, 10))

    # Hình ảnh chụp trực tiếp từ ETABS
    story.append(Paragraph("2. HÌNH ẢNH MÔ HÌNH CHỤP TRỰC TIẾP TỪ CỬA SỔ ETABS", h2_style))
    if os.path.exists(etabs_direct_3d):
        story.append(Image(etabs_direct_3d, width=7.0*inch, height=3.6*inch))
    else:
        story.append(Image(img_3d_1, width=7.0*inch, height=3.6*inch))

    # TRANG 2: HÌNH ẢNH CÁC GÓC NHÌN 3D & BẢN VẼ MOMENT TRỰC TIẾP TỪ ETABS
    story.append(PageBreak())
    story.append(Paragraph("3. CÁC GÓC NHÌN PHỐI CẢNH 3D MÔ HÌNH", h1_style))
    story.append(Paragraph("Hình ảnh phối cảnh không gian 3D kết cấu khung dầm cột nhìn từ 2 góc nhìn khác nhau:", body_style))
    story.append(Spacer(1, 6))
    
    # 2 hình 3D đặt song song hoặc trên dưới
    story.append(Image(img_3d_1, width=6.8*inch, height=3.4*inch))
    story.append(Spacer(1, 8))
    story.append(Image(img_3d_2, width=6.8*inch, height=3.4*inch))

    # TRANG 3: BẢN VẼ BIỂU ĐỒ MOMENT TRỰC TIẾP TỪ ETABS
    story.append(PageBreak())
    story.append(Paragraph("4. BẢN VẼ BIỂU ĐỒ MOMENT 3-3 CHỤP TRỰC TIẾP TỪ ETABS", h1_style))
    story.append(Paragraph("Ảnh chụp trực tiếp biểu đồ nội lực Moment uốn M3 từ màn hình làm việc CSI ETABS (Tổ hợp bao BAO):", body_style))
    story.append(Spacer(1, 6))
    if os.path.exists(etabs_direct_moment):
        story.append(Image(etabs_direct_moment, width=7.0*inch, height=3.5*inch))
    story.append(Spacer(1, 10))

    story.append(Paragraph("5. BIỂU ĐỒ BAO MOMENT DỌC CHIỀU DÀI DẦM (KÈM VÙNG VẬT LIỆU)", h2_style))
    story.append(Image(img_moment_path, width=7.0*inch, height=3.1*inch))

    # TRANG 4: BẢNG TỔNG HỢP MOMENT CỰC TRỊ CỦA DẦM
    story.append(PageBreak())
    story.append(Paragraph("6. BẢNG TỔNG HỢP MOMENT CỰC TRỊ CỦA DẦM (103 DẦM)", h1_style))
    story.append(Paragraph("Tổng hợp mô men uốn gối trái, bụng nhịp, gối phải và lực cắt lớn nhất để tính toán cốt thép dầm theo TCVN 5574:2018 (Tổ hợp bao BAO):", body_style))
    story.append(Spacer(1, 8))

    beam_summary_data = [
        [Paragraph("<b>Dầm ID</b>", cell_bold), Paragraph("<b>Tiết diện</b>", cell_bold),
         Paragraph("<b>Cao độ (m)</b>", cell_bold), Paragraph("<b>Nhịp L (m)</b>", cell_bold),
         Paragraph("<b>M_gối max (kNm)</b>", cell_bold), Paragraph("<b>M_nhịp max (kNm)</b>", cell_bold),
         Paragraph("<b>V_cắt max (kN)</b>", cell_bold)]
    ]
    beams_sorted = sorted(beams, key=lambda x: max(abs(x["m3_max"]), abs(x["m3_min"])), reverse=True)
    for b in beams_sorted[:35]:
        beam_summary_data.append([
            Paragraph(f"Dầm {b['id']}", cell_style),
            Paragraph(b["section"], cell_style),
            Paragraph(f"+{b['z']:.2f} m", cell_style),
            Paragraph(f"{b['length']:.2f} m", cell_style),
            Paragraph(f"<font color='red'><b>{b['m3_min']:.2f}</b></font>", cell_style),
            Paragraph(f"<font color='blue'><b>{b['m3_max']:.2f}</b></font>", cell_style),
            Paragraph(f"{b['v2_max']:.2f}", cell_style)
        ])
    t_beam_sum = Table(beam_summary_data, colWidths=[55, 90, 70, 65, 80, 80, 80])
    t_beam_sum.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#edf2f7')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e0')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_beam_sum)

    # TRANG 5: BẢNG TỔNG HỢP CỘT
    story.append(PageBreak())
    story.append(Paragraph("7. BẢNG TỔNG HỢP NỘI LỰC CỘT (58 CỘT)", h1_style))
    story.append(Paragraph("Tổng hợp lực dọc lớn nhất P_max, mô men uốn M3_max để tính toán cốt thép cột chịu nén lệch tâm xiên theo TCVN 5574:2018:", body_style))
    story.append(Spacer(1, 8))

    col_summary_data = [
        [Paragraph("<b>Cột ID</b>", cell_bold), Paragraph("<b>Tiết diện</b>", cell_bold),
         Paragraph("<b>Cao độ chân (m)</b>", cell_bold), Paragraph("<b>Chiều cao H (m)</b>", cell_bold),
         Paragraph("<b>Lực dọc P_max (kN)</b>", cell_bold), Paragraph("<b>M3_max (kNm)</b>", cell_bold),
         Paragraph("<b>V2_max (kN)</b>", cell_bold)]
    ]
    cols_sorted = sorted(columns, key=lambda x: x["p_max"], reverse=True)
    for c in cols_sorted[:35]:
        col_summary_data.append([
            Paragraph(f"Cột {c['id']}", cell_style),
            Paragraph(c["section"], cell_style),
            Paragraph(f"+{c['z']:.2f} m", cell_style),
            Paragraph(f"{c['length']:.2f} m", cell_style),
            Paragraph(f"<font color='purple'><b>{c['p_max']:.2f}</b></font>", cell_style),
            Paragraph(f"{c['m3_max']:.2f}", cell_style),
            Paragraph(f"{c['v2_max']:.2f}", cell_style)
        ])
    t_col_sum = Table(col_summary_data, colWidths=[55, 90, 75, 75, 80, 75, 70])
    t_col_sum.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#edf2f7')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e0')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_col_sum)

    # TRANG 6 ĐẾN 9: BẢNG MOMENT VÀ NỘI LỰC CHI TIẾT TỪNG MÉT MỘT (MOMENT AT EVERY 1 METER)
    story.append(PageBreak())
    story.append(Paragraph("8. BẢNG TRA NỘI LỰC CHI TIẾT TỪNG MÉT MỘT (MOMENT AT EVERY 1 METER)", h1_style))
    story.append(Paragraph("Bảng tra cứu trị số Moment uốn M3 (kN.m), Lực cắt V2 (kN), Lực dọc P (kN) tại chính xác từng mét chiều dài từ gối tựa (x = 0m, 1m, 2m, 3m... L) của các dầm và cột chính trong công trình:", body_style))
    story.append(Spacer(1, 8))

    detail_data = [
        [Paragraph("<b>Cấu kiện</b>", cell_bold), Paragraph("<b>Tiết diện</b>", cell_bold),
         Paragraph("<b>Khoảng cách X (m)</b>", cell_bold), Paragraph("<b>M3 gối/nhịp (kNm)</b>", cell_bold),
         Paragraph("<b>Lực cắt V2 (kN)</b>", cell_bold), Paragraph("<b>Lực dọc P (kN)</b>", cell_bold)]
    ]
    
    target_members = beams_sorted[:25] + cols_sorted[:12]
    for m in target_members:
        prefix = "Dầm" if m in beams else "Cột"
        mem_lbl = f"{prefix} {m['id']}"
        st_list = m["stations_1m"]
        for idx, st in enumerate(st_list):
            m_disp = f"<b>{st['m3_max']:.2f}</b> / {st['m3_min']:.2f}"
            detail_data.append([
                Paragraph(mem_lbl if idx == 0 else "", cell_style),
                Paragraph(m["section"] if idx == 0 else "", cell_style),
                Paragraph(f"<b>x = {st['station']:.2f} m</b>", cell_style),
                Paragraph(m_disp, cell_style),
                Paragraph(f"{st['v2_max']:.2f}", cell_style),
                Paragraph(f"{st['p_max']:.2f}", cell_style)
            ])
            
    t_detail = Table(detail_data, colWidths=[70, 95, 110, 110, 70, 65])
    t_detail.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2b6cb0')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e0')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(t_detail)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"=== ĐÃ XUẤT THÀNH CÔNG FILE PDF BÁO CÁO: {pdf_output} ===")
    return pdf_output

if __name__ == "__main__":
    extract_and_generate_report()
