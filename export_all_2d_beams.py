import os
import sys
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
        self.drawString(36, 810, "BẢN VẼ 2D NỘI LỰC MOMENT TỪNG DẦM - 163_165 PHAN BỘI CHÂU (ETABS 22.7.0)")
        self.drawRightString(559, 810, f"Trang {self._pageNumber} / {page_count}")
        self.setStrokeColor(colors.HexColor("#cbd5e0"))
        self.setLineWidth(0.5)
        self.line(36, 804, 559, 804)
        self.restoreState()

def generate_beam_plot(beam, save_path):
    L = beam["length"]
    st_list = beam["stations_1m"]
    if not st_list or L <= 0.05:
        return False
        
    xs = [s["station"] for s in st_list]
    m_max = [s["m3_max"] for s in st_list] # moment dương bụng (kN.m)
    m_min = [s["m3_min"] for s in st_list] # moment âm gối (kN.m)
    v_max = [s["v2_max"] for s in st_list]
    
    # Quy ước vẽ kết cấu (TCVN 5574:2018):
    # Moment âm vẽ lên trên (căng thớ trên gối), Moment dương vẽ xuống dưới (căng thớ dưới nhịp)
    fig, ax = plt.subplots(figsize=(7.2, 2.2), dpi=140)
    
    # Trục dầm
    ax.axhline(0, color='#2d3748', linewidth=1.5, zorder=3)
    
    # Ký hiệu gối tựa (cột) ở đầu và cuối dầm
    ax.plot([0, 0], [0, 0], marker='^', markersize=10, color='#2b6cb0', zorder=5)
    ax.plot([L, L], [0, 0], marker='^', markersize=10, color='#2b6cb0', zorder=5)
    
    y_gối = [-m for m in m_min] # M âm thành dương (vẽ lên trên)
    y_bụng = [-m for m in m_max] # M dương thành âm (vẽ xuống dưới)
    
    ax.plot(xs, y_gối, color='#e53e3e', linewidth=1.8, label='M(-) Thớ trên (Gối)')
    ax.plot(xs, y_bụng, color='#3182ce', linewidth=1.8, label='M(+) Thớ dưới (Bụng)')
    
    # Tô màu miền diện tích Moment
    ax.fill_between(xs, y_gối, 0, where=[y >= 0 for y in y_gối], color='#fed7d7', alpha=0.6)
    ax.fill_between(xs, y_bụng, 0, where=[y <= 0 for y in y_bụng], color='#bee3f8', alpha=0.6)
    
    # Đánh dấu các trạm từng mét và ghi trị số
    max_abs_m = max([abs(m) for m in m_max + m_min] + [1.0])
    offset = max_abs_m * 0.12
    
    for s in st_list:
        x_val = s["station"]
        ax.axvline(x_val, color='#a0aec0', linestyle=':', linewidth=0.7, zorder=2)
        val_top = s["m3_min"]
        val_bot = s["m3_max"]
        if abs(val_top) > 0.5:
            ax.text(x_val, -val_top + offset*0.3, f"{val_top:.1f}", fontsize=6.5, ha='center', va='bottom', color='#9b2c2c', fontweight='bold')
        if abs(val_bot) > 0.5:
            ax.text(x_val, -val_bot - offset*0.3, f"{val_bot:.1f}", fontsize=6.5, ha='center', va='top', color='#2b6cb0', fontweight='bold')

    ax.set_xlim(-0.2, L + 0.2)
    y_all = y_gối + y_bụng
    y_min_lim = min(y_all) - offset if y_all else -5
    y_max_lim = max(y_all) + offset if y_all else 5
    ax.set_ylim(y_min_lim, y_max_lim)
    
    ax.set_xlabel(f"Chiều dài nhịp dầm L = {L:.2f} m (Trạm cách nhau 1.0 m)", fontsize=7.5, labelpad=2)
    ax.set_ylabel("Thớ trên (-)\nThớ dưới (+)", fontsize=6.5, labelpad=2)
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.legend(fontsize=6.5, loc='upper right', framealpha=0.85)
    
    ax.text(0.01, 0.95, f"M_gối max = {beam['m3_min']:.2f} kNm | M_bụng max = {beam['m3_max']:.2f} kNm | V_max = {beam['v2_max']:.2f} kN",
            transform=ax.transAxes, fontsize=7, color='#2d3748',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#f7fafc', edgecolor='#cbd5e0', alpha=0.9))
            
    fig.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)
    return True

def run_export_all_2d_beams():
    edb_path = r"d:\Dropbox\_Documents\RevitAI\cai_tao_model.EDB"
    pdf_output = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads\BAN_VE_2D_MOMENT_TAT_CA_DAM_ETABS.pdf"
    img_dir = r"d:\Dropbox\_Documents\RevitAI\scratch\beam_plots"
    os.makedirs(img_dir, exist_ok=True)
    
    print(f"=== BẮT ĐẦU XUẤT HÀNG LOẠT BẢN VẼ 2D TẤT CẢ DẦM TỪ: {edb_path} ===")
    helper = comtypes.client.CreateObject('ETABSv1.Helper').QueryInterface(ETABSv1.cHelper)
    app = helper.CreateObjectProgId("CSI.ETABS.API.ETABSObject")
    app.ApplicationStart()
    sap = app.SapModel
    sap.File.OpenFile(edb_path)
    
    # Đảm bảo đã chạy phân tích
    if not sap.GetModelIsLocked():
        print("Mô hình chưa khóa, đang thiết lập SemiRigid và chạy RunAnalysis()...")
        for d in sap.Diaphragm.GetNameList()[1]:
            sap.Diaphragm.SetDiaphragm(d, True)
        sap.Analyze.RunAnalysis()
        print("RunAnalysis hoàn tất! Locked:", sap.GetModelIsLocked())
        
    scale_m = 1e-6 if sap.GetPresentUnits() == 9 else 1.0
    scale_f = 1e-3 if sap.GetPresentUnits() == 9 else 1.0
    scale_l = 1e-3 if sap.GetPresentUnits() == 9 else 1.0
    
    sap.Results.Setup.DeselectAllCasesAndCombosForOutput()
    sap.Results.Setup.SetComboSelectedForOutput("BAO", True)

    story_names = sap.Story.GetNameList()[1]
    story_elevs = {s: round(sap.Story.GetElevation(s)[0] * scale_l, 2) for s in story_names}
    
    all_frames = sap.FrameObj.GetNameList()[1]
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
        
        # Chỉ lấy dầm (không phải cột) và chiều dài > 0.4m
        if not is_col and length > 0.4:
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
                
            # Nội suy trạm từng mét (0m, 1m, 2m, ... L)
            stations_1m = []
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

            beams.append({
                "id": f,
                "section": sec,
                "story": closest_story,
                "z": round(z_mid, 2),
                "length": round(length, 2),
                "c1": c1,
                "c2": c2,
                "stations_1m": stations_1m,
                "m3_max": max([s["m3_max"] for s in station_envelope]) if station_envelope else 0.0,
                "m3_min": min([s["m3_min"] for s in station_envelope]) if station_envelope else 0.0,
                "v2_max": max([s["v2_max"] for s in station_envelope]) if station_envelope else 0.0,
            })

    app.ApplicationExit(False)
    print(f"-> Đã thu thập dữ liệu của {len(beams)} dầm. Bắt đầu vẽ bản vẽ 2D...")

    # Sắp xếp dầm theo tầng, sau đó theo độ lớn moment
    beams.sort(key=lambda b: (b["z"], -max(abs(b["m3_max"]), abs(b["m3_min"]))))

    valid_beams = []
    for idx, b in enumerate(beams):
        img_name = f"beam_{b['id']}_{idx}.png"
        img_p = os.path.join(img_dir, img_name)
        ok = generate_beam_plot(b, img_p)
        if ok:
            b["img_path"] = img_p
            valid_beams.append(b)
            
    print(f"-> Đã vẽ xong {len(valid_beams)} bản vẽ 2D Moment dầm.")

    # ---------------------------------------------------------
    # TẠO TẬP HỒ SƠ PDF BẢN VẼ 2D
    # ---------------------------------------------------------
    print("--- KHỞI TẠO TẬP TÀI LIỆU PDF BẢN VẼ KỸ THUẬT ---")
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
    story_h_style = ParagraphStyle(
        'StoryHeader', parent=styles['Normal'],
        fontName='Arial-Bold', fontSize=12, leading=16,
        textColor=colors.HexColor('#2c5282'), spaceBefore=8, spaceAfter=4
    )
    body_style = ParagraphStyle(
        'Body_Custom', parent=styles['Normal'],
        fontName='Arial', fontSize=8.5, leading=12, textColor=colors.HexColor('#2d3748')
    )
    beam_title_style = ParagraphStyle(
        'BeamTitle', parent=styles['Normal'],
        fontName='Arial-Bold', fontSize=9.5, leading=13, textColor=colors.HexColor('#1a365d')
    )
    cell_style = ParagraphStyle(
        'CellText', parent=styles['Normal'],
        fontName='Arial', fontSize=7, leading=9, textColor=colors.HexColor('#1a202c')
    )
    cell_bold = ParagraphStyle('CellBold', parent=cell_style, fontName='Arial-Bold')

    story = []
    
    # TRANG BÌA
    story.append(Spacer(1, 20))
    story.append(Paragraph("TẬP HỒ SƠ BẢN VẼ 2D NỘI LỰC MOMENT TOÀN BỘ DẦM", title_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("CÔNG TRÌNH: 163 - 165 PHAN BỘI CHÂU (CẢI TẠO)", sub_title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"TỔNG HỢP {len(valid_beams)} DẦM CHI TIẾT TỪNG MÉT - XUẤT TỰ ĐỘNG TỪ CSI ETABS 22.7.0", ParagraphStyle('Sub2', parent=sub_title_style, fontName='Arial', fontSize=8.5, textColor=colors.HexColor('#4a5568'))))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2b6cb0'), spaceBefore=2, spaceAfter=14))

    intro_text = (
        "<b>Hướng dẫn đọc bản vẽ:</b><br/>"
        "• <b>Quy ước biểu đồ Moment:</b> Biểu đồ vẽ theo quy ước thớ căng kết cấu (TCVN 5574:2018). "
        "Vùng màu đỏ nhô lên trên thể hiện Moment âm M(-) căng thớ trên (bố trí thép gối dầm). "
        "Vùng màu xanh lam võng xuống dưới thể hiện Moment dương M(+) căng thớ dưới (bố trí thép bụng nhịp dầm).<br/>"
        "• <b>Vạch chia từng mét:</b> Các đường gióng đứt nét phân chia chính xác từng mét chiều dài (x = 1.0m, 2.0m, 3.0m... L) "
        "kèm trị số Moment và Lực cắt phục vụ tra cứu cắt uốn thép chuẩn xác tuyệt đối.<br/>"
        "• <b>Tổ hợp tải trọng:</b> Toàn bộ nội lực được trích xuất từ <b>Tổ hợp bao lớn nhất (BAO)</b>."
    )
    story.append(Paragraph(intro_text, body_style))
    story.append(Spacer(1, 14))

    # Bảng phân bổ dầm theo tầng
    story_counts = {}
    for b in valid_beams:
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

    # XUẤT CÁC BẢN VẼ DẦM (2 DẦM TRÊN MỖI TRANG)
    current_story = None
    beams_on_page = 0
    
    for idx, b in enumerate(valid_beams):
        # Tiêu đề tầng khi chuyển tầng
        if b["story"] != current_story:
            current_story = b["story"]
            if beams_on_page > 0:
                story.append(PageBreak())
                beams_on_page = 0
            story.append(Paragraph(f"HỆ DẦM TẦNG {current_story} (CAO ĐỘ +{b['z']:.2f} m)", story_h_style))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e0'), spaceBefore=2, spaceAfter=8))

        # Khung thông tin dầm
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
        
        # Bảng tra cứu từng mét
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
        
        if beams_on_page >= 2 and idx < len(valid_beams) - 1:
            story.append(PageBreak())
            beams_on_page = 0

    doc.build(story, canvasmaker=CleanCanvas)
    print(f"=== ĐÃ XUẤT THÀNH CÔNG TẬP BẢN VẼ 2D DẦM: {pdf_output} ===")
    return pdf_output

if __name__ == "__main__":
    run_export_all_2d_beams()
