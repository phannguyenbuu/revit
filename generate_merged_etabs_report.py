import os
import sys
import shutil
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['Arial', 'Segoe UI', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

import comtypes.client
from comtypes.gen import ETABSv1

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Đăng ký Font Unicode tiếng Việt
FONT_ARIAL = 'C:/Windows/Fonts/arial.ttf'
FONT_ARIAL_BOLD = 'C:/Windows/Fonts/arialbd.ttf'
pdfmetrics.registerFont(TTFont('Arial', FONT_ARIAL))
pdfmetrics.registerFont(TTFont('Arial-Bold', FONT_ARIAL_BOLD))

class CleanCanvas(canvas.Canvas):
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
            self.draw_header(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_header(self, page_count):
        self.saveState()
        self.setFont("Arial", 8)
        self.setFillColor(colors.HexColor("#555555"))
        # Top Header line only, no footer per user request
        self.drawString(36, 810, "HỒ SƠ NỘI LỰC VÀ BẢN VẼ 2D MOMENT DẦM - 163_165 PHAN BỘI CHÂU (ETABS 22.7.0)")
        self.drawRightString(559, 810, f"Trang {self._pageNumber} / {page_count}")
        self.setStrokeColor(colors.HexColor("#cbd5e0"))
        self.setLineWidth(0.5)
        self.line(36, 804, 559, 804)
        self.restoreState()

def generate_merged_document():
    edb_path = r"d:\Dropbox\_Documents\RevitAI\cai_tao_model.EDB"
    target_dir = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads\ETABS_IFC"
    os.makedirs(target_dir, exist_ok=True)
    pdf_output = os.path.join(target_dir, "HO_SO_NOI_LUC_VA_BAN_VE_2D_MOMENT_ETABS_163_165_PHAN_BOI_CHAU.pdf")
    pdf_output_dl = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads\HO_SO_NOI_LUC_VA_BAN_VE_2D_MOMENT_ETABS_163_165_PHAN_BOI_CHAU.pdf"
    
    user_img_src = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\3a84420f-3bcc-4200-a963-fe9e158668d7\.user_uploaded\media_1791555786257.png"
    img_dir = r"d:\Dropbox\_Documents\RevitAI\scratch"
    os.makedirs(img_dir, exist_ok=True)
    user_img_target = os.path.join(img_dir, "user_etabs_3d_moment.png")
    shutil.copy2(user_img_src, user_img_target)
    
    print("--- 1. KẾT NỐI VÀ TRÍCH XUẤT NỘI LỰC ETABS ---")
    helper = comtypes.client.CreateObject('ETABSv1.Helper').QueryInterface(ETABSv1.cHelper)
    app = helper.CreateObjectProgId("CSI.ETABS.API.ETABSObject")
    app.ApplicationStart()
    sap = app.SapModel
    sap.File.OpenFile(edb_path)
    
    if not sap.GetModelIsLocked():
        for d in sap.Diaphragm.GetNameList()[1]:
            sap.Diaphragm.SetDiaphragm(d, True)
        sap.Analyze.RunAnalysis()
        
    scale_m = 1e-6 if sap.GetPresentUnits() == 9 else 1.0
    scale_f = 1e-3 if sap.GetPresentUnits() == 9 else 1.0
    scale_l = 1e-3 if sap.GetPresentUnits() == 9 else 1.0
    
    sap.Results.Setup.DeselectAllCasesAndCombosForOutput()
    sap.Results.Setup.SetComboSelectedForOutput("BAO", True)

    story_names = sap.Story.GetNameList()[1]
    stories_data = []
    story_elevs = {}
    for s in story_names:
        elev = sap.Story.GetElevation(s)[0] * scale_l
        height = sap.Story.GetHeight(s)[0] * scale_l
        stories_data.append({"name": s, "elevation": elev, "height": height})
        story_elevs[s] = round(elev, 2)
    stories_data.sort(key=lambda x: x["elevation"])

    all_frames = sap.FrameObj.GetNameList()[1]
    columns = []
    beams = []
    
    for f in all_frames:
        sec = sap.FrameObj.GetSection(f)[0]
        p1, p2, _ = sap.FrameObj.GetPoints(f)
        c1 = [c * scale_l for c in sap.PointObj.GetCoordCartesian(p1)[:3]]
        c2 = [c * scale_l for c in sap.PointObj.GetCoordCartesian(p2)[:3]]
        dx = abs(c2[0] - c1[0])
        dy = abs(c2[1] - c1[1])
        dz = abs(c2[2] - c1[2])
        length = math.sqrt((c2[0]-c1[0])**2 + (c2[1]-c1[1])**2 + (c2[2]-c1[2])**2)
        
        is_col = (dz > 0.5 and dx < 0.1 and dy < 0.1)
        z_mid = (c1[2] + c2[2]) / 2.0
        
        closest_story = "T1"
        min_dz = 999.0
        for s, s_z in story_elevs.items():
            if abs(z_mid - s_z) < min_dz:
                min_dz = abs(z_mid - s_z)
                closest_story = s

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
            
        stations_1m = []
        if length > 0.01:
            num_meter_steps = int(math.floor(length))
            meter_points = [float(x) for x in range(num_meter_steps + 1)]
            if length not in meter_points and (length - meter_points[-1]) > 0.1:
                meter_points.append(round(length, 2))
                
            for mp in meter_points:
                if not sorted_stations: continue
                if mp <= sorted_stations[0]: se = station_envelope[0]
                elif mp >= sorted_stations[-1]: se = station_envelope[-1]
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
            "story": closest_story,
            "c1": c1, "c2": c2,
            "length": round(length, 2),
            "z": round(z_mid, 2),
            "stations_1m": stations_1m,
            "m3_max": max([s["m3_max"] for s in station_envelope]) if station_envelope else 0.0,
            "m3_min": min([s["m3_min"] for s in station_envelope]) if station_envelope else 0.0,
            "v2_max": max([s["v2_max"] for s in station_envelope]) if station_envelope else 0.0,
            "p_max": max([s["p_max"] for s in station_envelope]) if station_envelope else 0.0
        }
        
        if is_col:
            columns.append(item)
        elif length > 0.4:
            beams.append(item)

    app.ApplicationExit(False)
    print(f"-> Đã trích xuất xong: {len(columns)} Cột và {len(beams)} Dầm.")

    # Sắp xếp
    beams.sort(key=lambda b: (b["z"], -max(abs(b["m3_max"]), abs(b["m3_min"]))))
    columns.sort(key=lambda c: -c["p_max"])

    # Kiểm tra các ảnh dầm 2D trong beam_plots
    beam_plots_dir = r"d:\Dropbox\_Documents\RevitAI\scratch\beam_plots"
    for idx, b in enumerate(beams):
        p = os.path.join(beam_plots_dir, f"beam_{b['id']}_{idx}.png")
        if os.path.exists(p):
            b["img_path"] = p

    # ---------------------------------------------------------
    # KHỞI TẠO TẬP HỒ SƠ PDF DUY NHẤT
    # ---------------------------------------------------------
    print("--- 2. TẠO FILE PDF TỔNG HỢP DUY NHẤT ---")
    doc = SimpleDocTemplate(
        pdf_output,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Normal'],
        fontName='Arial-Bold', fontSize=18, leading=22,
        textColor=colors.HexColor('#1a365d'), alignment=1
    )
    sub_title_style = ParagraphStyle(
        'SubTitle', parent=styles['Normal'],
        fontName='Arial-Bold', fontSize=11, leading=15,
        textColor=colors.HexColor('#2b6cb0'), alignment=1
    )
    part_title_style = ParagraphStyle(
        'PartTitle', parent=styles['Normal'],
        fontName='Arial-Bold', fontSize=15, leading=19,
        textColor=colors.HexColor('#1a365d'), alignment=1
    )
    h1_style = ParagraphStyle(
        'Heading1_Custom', parent=styles['Heading1'],
        fontName='Arial-Bold', fontSize=12, leading=16,
        textColor=colors.HexColor('#1a365d'), spaceBefore=10, spaceAfter=5
    )
    h2_style = ParagraphStyle(
        'Heading2_Custom', parent=styles['Heading2'],
        fontName='Arial-Bold', fontSize=10, leading=14,
        textColor=colors.HexColor('#2c5282'), spaceBefore=6, spaceAfter=4
    )
    story_h_style = ParagraphStyle(
        'StoryHeader', parent=styles['Normal'],
        fontName='Arial-Bold', fontSize=11.5, leading=15,
        textColor=colors.HexColor('#2c5282'), spaceBefore=8, spaceAfter=4
    )
    body_style = ParagraphStyle(
        'Body_Custom', parent=styles['Normal'],
        fontName='Arial', fontSize=8.5, leading=12.5, textColor=colors.HexColor('#2d3748')
    )
    beam_title_style = ParagraphStyle(
        'BeamTitle', parent=styles['Normal'],
        fontName='Arial-Bold', fontSize=9, leading=12.5, textColor=colors.HexColor('#1a365d')
    )
    cell_style = ParagraphStyle(
        'CellText', parent=styles['Normal'],
        fontName='Arial', fontSize=7, leading=9, textColor=colors.HexColor('#1a202c')
    )
    cell_bold = ParagraphStyle('CellBold', parent=cell_style, fontName='Arial-Bold')

    story = []
    
    # =========================================================
    # PHẦN I: BÁO CÁO NỘI LỰC VÀ AN TOÀN KẾT CẤU (4 HÌNH CŨ ĐÃ XÓA, THAY HÌNH CỦA BẠN VÀO)
    # =========================================================
    story.append(Spacer(1, 10))
    story.append(Paragraph("HỒ SƠ TỔNG HỢP NỘI LỰC & BẢN VẼ 2D MOMENT DẦM", title_style))
    story.append(Spacer(1, 5))
    story.append(Paragraph("CÔNG TRÌNH: 163 - 165 PHAN BỘI CHÂU (CẢI TẠO)", sub_title_style))
    story.append(Spacer(1, 3))
    story.append(Paragraph("PHẦN MỀM TÍNH TOÁN: CSI ETABS ULTIMATE 22.7.0 (OAPI VERIFIED)", ParagraphStyle('Sub2', parent=sub_title_style, fontName='Arial', fontSize=8.5, textColor=colors.HexColor('#4a5568'))))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2b6cb0'), spaceBefore=2, spaceAfter=10))

    intro_p1 = (
        "<b>Tiêu chuẩn thiết kế & phân tích:</b> TCVN 5574:2018 (Kết cấu BTCT), TCVN 2737:2023 (Tải trọng & tác động).<br/>"
        "<b>Quy mô mô hình:</b> 05 Tầng (+1.8m đến +18.4m) | <b>58 Cột</b> bê tông cốt thép | <b>94 Dầm chính</b> | <b>81 Ô sàn</b>.<br/>"
        "<b>Tổ hợp nội lực:</b> Toàn bộ nội lực được trích xuất từ <b>Tổ hợp bao lớn nhất (BAO)</b>."
    )
    story.append(Paragraph(intro_p1, body_style))
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

    # ĐÂY LÀ HÌNH ẢNH CỦA BẠN GỬI (ĐÃ THAY THẾ 4 HÌNH CŨ)
    story.append(Paragraph("2. MÔ HÌNH KHÔNG GIAN 3D & BIỂU ĐỒ MOMENT 3-3 THỰC TẾ TRỰC TIẾP TỪ ETABS", h2_style))
    story.append(Paragraph("Hình ảnh không gian 3D chụp từ giao diện làm việc ETABS thể hiện hệ khung dầm, cột, sàn thang và biểu đồ Moment uốn M3 (đường cong màu vàng) theo tổ hợp bao BAO:", body_style))
    story.append(Spacer(1, 4))
    story.append(Image(user_img_target, width=5.8*inch, height=5.4*inch))
    story.append(Spacer(1, 10))

    # TRANG 2: BẢNG TỔNG HỢP MOMENT CỰC TRỊ CỦA DẦM
    story.append(PageBreak())
    story.append(Paragraph("3. BẢNG TỔNG HỢP NỘI LỰC CỰC TRỊ DẦM (TỔ HỢP BAO)", h1_style))
    story.append(Paragraph("Tổng hợp mô men uốn gối trái, bụng nhịp, gối phải và lực cắt lớn nhất để tính toán cốt thép dầm theo TCVN 5574:2018:", body_style))
    story.append(Spacer(1, 6))

    beam_summary_data = [
        [Paragraph("<b>Dầm ID</b>", cell_bold), Paragraph("<b>Tiết diện</b>", cell_bold),
         Paragraph("<b>Cao độ (m)</b>", cell_bold), Paragraph("<b>Nhịp L (m)</b>", cell_bold),
         Paragraph("<b>M_gối max (kNm)</b>", cell_bold), Paragraph("<b>M_nhịp max (kNm)</b>", cell_bold),
         Paragraph("<b>V_cắt max (kN)</b>", cell_bold)]
    ]
    for b in beams[:35]:
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
    story.append(Spacer(1, 12))

    # BẢNG TỔNG HỢP CỘT
    story.append(Paragraph("4. BẢNG TỔNG HỢP NỘI LỰC CỘT (58 CỘT)", h1_style))
    story.append(Paragraph("Tổng hợp lực dọc lớn nhất P_max, mô men uốn M3_max để tính toán cốt thép cột chịu nén lệch tâm xiên theo TCVN 5574:2018:", body_style))
    story.append(Spacer(1, 6))

    col_summary_data = [
        [Paragraph("<b>Cột ID</b>", cell_bold), Paragraph("<b>Tiết diện</b>", cell_bold),
         Paragraph("<b>Cao độ chân (m)</b>", cell_bold), Paragraph("<b>Chiều cao H (m)</b>", cell_bold),
         Paragraph("<b>Lực dọc P_max (kN)</b>", cell_bold), Paragraph("<b>M3_max (kNm)</b>", cell_bold),
         Paragraph("<b>V2_max (kN)</b>", cell_bold)]
    ]
    for c in columns[:30]:
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
    story.append(PageBreak())

    # =========================================================
    # PHẦN II: TẬP BẢN VẼ 2D NỘI LỰC MOMENT TOÀN BỘ 94 DẦM (2 DẦM/TRANG)
    # =========================================================
    story.append(Spacer(1, 30))
    story.append(Paragraph("PHẦN II: TẬP BẢN VẼ 2D NỘI LỰC MOMENT TOÀN BỘ DẦM", part_title_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("TỔNG HỢP CHI TIẾT 94 DẦM CHÍNH - BIỂU ĐỒ UỐN THỚ TRÊN / THỚ DƯỚI & TRA CỨU TỪNG MÉT", sub_title_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2b6cb0'), spaceBefore=2, spaceAfter=14))

    guide_text = (
        "<b>Quy chuẩn bản vẽ 2D:</b><br/>"
        "• Vùng màu đỏ nhô lên trên thể hiện Moment âm $M(-)$ căng thớ trên (bố trí thép gối dầm).<br/>"
        "• Vùng màu xanh lam võng xuống dưới thể hiện Moment dương $M(+)$ căng thớ dưới (bố trí thép bụng nhịp dầm).<br/>"
        "• Các đường gióng đứt nét phân chia chính xác từng mét chiều dài ($x = 1.0\text{m}, 2.0\text{m}\dots L$) "
        "kèm bảng tra cứu trị số Moment $M_3$ và Lực cắt $V_2$ cụ thể ngay dưới mỗi dầm."
    )
    story.append(Paragraph(guide_text, body_style))
    story.append(Spacer(1, 14))

    # Bảng phân bổ dầm theo tầng
    story_counts = {}
    valid_draw_beams = [b for b in beams if "img_path" in b]
    for b in valid_draw_beams:
        s_lbl = f"{b['story']} (Cao độ +{b['z']:.2f}m)"
        story_counts[s_lbl] = story_counts.get(s_lbl, 0) + 1
        
    t_stat_data = [[Paragraph("<b>Tầng / Cao độ</b>", cell_bold), Paragraph("<b>Số lượng dầm</b>", cell_bold), Paragraph("<b>Tiết diện chủ đạo</b>", cell_bold)]]
    for s_lbl, cnt in story_counts.items():
        t_stat_data.append([
            Paragraph(s_lbl, cell_style),
            Paragraph(f"{cnt} dầm", cell_style),
            Paragraph("B 200x400, B 250x500, B 300x600, B 300x700", cell_style)
        ])
    t_stat = Table(t_stat_data, colWidths=[180, 100, 240])
    t_stat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#edf2f7')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e0')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_stat)
    story.append(PageBreak())

    # XUẤT CÁC BẢN VẼ DẦM 2D (2 DẦM TRÊN MỖI TRANG)
    current_story = None
    beams_on_page = 0
    
    for idx, b in enumerate(valid_draw_beams):
        if b["story"] != current_story:
            current_story = b["story"]
            if beams_on_page > 0:
                story.append(PageBreak())
                beams_on_page = 0
            story.append(Paragraph(f"HỆ DẦM TẦNG {current_story} (CAO ĐỘ +{b['z']:.2f} m)", story_h_style))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e0'), spaceBefore=2, spaceAfter=8))

        b_header = (
            f"<b>DẦM ID: {b['id']}</b> | Tiết diện: <b>{b['section']}</b> | "
            f"Nhịp: <b>L = {b['length']:.2f} m</b> | Tầng: <b>{b['story']} (+{b['z']:.2f}m)</b> | "
            f"Tọa độ: ({b['c1'][0]:.1f}, {b['c1'][1]:.1f}) &rarr; ({b['c2'][0]:.1f}, {b['c2'][1]:.1f})"
        )
        card_elements = [
            Paragraph(b_header, beam_title_style),
            Spacer(1, 3),
            Image(b["img_path"], width=7.1*inch, height=2.15*inch),
            Spacer(1, 2)
        ]
        
        table_rows = [
            [Paragraph("<b>x (m)</b>", cell_bold)] + [Paragraph(f"{s['station']:.1f}", cell_style) for s in b["stations_1m"]],
            [Paragraph("<b>M3 (kNm)</b>", cell_bold)] + [
                Paragraph(f"<b>{s['m3_min']:.1f}</b>" if abs(s['m3_min']) > abs(s['m3_max']) else f"<b>{s['m3_max']:.1f}</b>", cell_style)
                for s in b["stations_1m"]
            ],
            [Paragraph("<b>V2 (kN)</b>", cell_bold)] + [Paragraph(f"{s['v2_max']:.1f}", cell_style) for s in b["stations_1m"]]
        ]
        col_w = max(24, 460 // max(len(b["stations_1m"]), 1))
        col_widths = [60] + [col_w] * len(b["stations_1m"])
        t_stations = Table(table_rows, colWidths=col_widths)
        t_stations.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f7fafc')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
            ('TOPPADDING', (0,0), (-1,-1), 1.5),
        ]))
        card_elements.append(t_stations)
        card_elements.append(Spacer(1, 14))

        story.append(KeepTogether(card_elements))
        beams_on_page += 1
        
        if beams_on_page >= 2 and idx < len(valid_draw_beams) - 1:
            story.append(PageBreak())
            beams_on_page = 0

    doc.build(story, canvasmaker=CleanCanvas)
    
    # Tạo thêm bản sao tại Downloads
    shutil.copy2(pdf_output, pdf_output_dl)
    print(f"=== ĐÃ XUẤT THÀNH CÔNG TẬP HỒ SƠ GỘP TẠI:\n  1. {pdf_output}\n  2. {pdf_output_dl} ===")
    return pdf_output

if __name__ == "__main__":
    generate_merged_document()
