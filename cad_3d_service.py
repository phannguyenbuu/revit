"""
AutoCAD 3D OBJ & Vision Detection Service
Wraps:
1. Windows Clipboard OLE -> DWG -> DXF extraction via PowerShell & AutoCAD accoreconsole
2. 2D Computer Vision Floorplan Detection (Doors, Windows, Columns, Walls)
3. 3D Wavefront OBJ Generator (Walls, Doors, Windows, Multi-flight Stairs, 3 Tam Cap Steps, Slope Ramp)
4. Model inspection and metadata extraction via Trimesh
"""

import sys
import os
import struct
import subprocess
import json
import shutil
from pathlib import Path
import numpy as np

# Reconfigure stdout for utf-8 if possible
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
AUTOCAD_3D_OBJ_DIR = os.path.join(CURRENT_DIR, "autocad_3d_obj")
DEFAULT_VISION_DIR = os.path.join(AUTOCAD_3D_OBJ_DIR, "vision_output")
DEFAULT_MODELS_DIR = os.path.join(AUTOCAD_3D_OBJ_DIR, "models_export")
DEFAULT_ACAD_DIR = r"C:\Program Files\Autodesk\AutoCAD 2022"


def is_acad_available():
    accore = os.path.join(DEFAULT_ACAD_DIR, "accoreconsole.exe")
    return os.path.exists(accore)


def check_clipboard_has_autocad():
    """Kiểm tra xem Clipboard hiện tại có chứa đối tượng AutoCAD (Embed Source) hay không."""
    ps_cmd = """
    Add-Type -AssemblyName System.Windows.Forms
    $data = [System.Windows.Forms.Clipboard]::GetDataObject()
    if ($null -eq $data) { exit 1 }
    if ($data.GetDataPresent('Embed Source')) { exit 0 }
    exit 2
    """
    try:
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, timeout=5)
        return res.returncode == 0
    except Exception:
        return False


def extract_clipboard_ole(out_bin_path):
    """Trích xuất stream AutoCAD OLE từ Clipboard Windows qua PowerShell."""
    os.makedirs(os.path.dirname(os.path.abspath(out_bin_path)), exist_ok=True)
    out_escaped = out_bin_path.replace("'", "''")
    ps_cmd = f"""
    Add-Type -AssemblyName System.Windows.Forms
    $data = [System.Windows.Forms.Clipboard]::GetDataObject()
    if ($null -eq $data) {{ exit 1 }}
    if ($data.GetDataPresent('Embed Source')) {{
        $ms = $data.GetData('Embed Source')
        if ($ms -is [System.IO.MemoryStream]) {{
            [System.IO.File]::WriteAllBytes('{out_escaped}', $ms.ToArray())
            exit 0
        }}
    }}
    exit 2
    """
    res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, timeout=10)
    if res.returncode != 0 or not os.path.exists(out_bin_path):
        raise RuntimeError("Không tìm thấy dữ liệu AutoCAD OLE ('Embed Source') trong Clipboard! Hãy quét chọn đối tượng trong AutoCAD và bấm Ctrl+C.")
    return os.path.getsize(out_bin_path)


def extract_dwg_from_ole(ole_path, out_dwg_path):
    """Trích xuất file DWG nguyên bản từ OLE Compound Document (CFBF format)."""
    os.makedirs(os.path.dirname(os.path.abspath(out_dwg_path)), exist_ok=True)
    with open(ole_path, "rb") as f:
        data = f.read()

    if not data.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        raise ValueError("File không phải định dạng OLE Compound File (CFBF)")

    sector_shift = struct.unpack_from("<H", data, 30)[0]
    sector_size = 1 << sector_shift
    first_dir_sector = struct.unpack_from("<I", data, 48)[0]
    mini_cutoff = struct.unpack_from("<I", data, 56)[0]

    fat_sectors = [struct.unpack_from("<I", data, 76 + i*4)[0] for i in range(109) if struct.unpack_from("<I", data, 76 + i*4)[0] < 0xFFFFFFFD]
    fat = []
    for sec in fat_sectors:
        off = (sec + 1) * sector_size
        fat.extend(struct.unpack(f"<{sector_size // 4}I", data[off:off+sector_size]))

    def get_chain(start_sec):
        chain = []
        sec = start_sec
        while sec < 0xFFFFFFFD and sec < len(fat):
            chain.append(sec)
            sec = fat[sec]
        return chain

    dir_chain = get_chain(first_dir_sector)
    dir_data = b"".join(data[(s+1)*sector_size : (s+2)*sector_size] for s in dir_chain)

    dwg_found = False
    for i in range(len(dir_data) // 128):
        eb = dir_data[i*128 : (i+1)*128]
        n_len = struct.unpack_from("<H", eb, 64)[0]
        if n_len <= 2:
            continue
        name = eb[:n_len-2].decode("utf-16le", errors="replace")
        obj_type = eb[66]
        start_sec = struct.unpack_from("<I", eb, 116)[0]
        size = struct.unpack_from("<Q", eb, 120)[0]

        if obj_type == 2 and size >= mini_cutoff:
            s_chain = get_chain(start_sec)
            s_data = b"".join(data[(s+1)*sector_size : (s+2)*sector_size] for s in s_chain)[:size]
            if s_data.startswith(b"AC10"):
                with open(out_dwg_path, "wb") as f_out:
                    f_out.write(s_data)
                dwg_found = True
                break

    if not dwg_found:
        raise RuntimeError("Không tìm thấy stream DWG (AC10xx) trong dữ liệu OLE!")
    return os.path.getsize(out_dwg_path)


def convert_dwg_to_dxf(dwg_path, out_dxf_path, acad_dir=DEFAULT_ACAD_DIR):
    """Dùng accoreconsole để chuyển DWG sang DXF chuẩn 100%."""
    os.makedirs(os.path.dirname(os.path.abspath(out_dxf_path)), exist_ok=True)
    accore = os.path.join(acad_dir, "accoreconsole.exe")
    if not os.path.exists(accore):
        raise FileNotFoundError(f"Không tìm thấy accoreconsole.exe tại {accore}")

    scr_path = os.path.join(os.path.dirname(out_dxf_path), "_temp_export.scr")
    formatted_dxf = out_dxf_path.replace("\\", "/")
    with open(scr_path, "w", encoding="utf-8") as f:
        f.write(f'DXFOUT "{formatted_dxf}" 16\nQUIT\n')

    cmd = [accore, "/i", dwg_path, "/s", scr_path]
    subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if os.path.exists(scr_path):
        try:
            os.remove(scr_path)
        except Exception:
            pass

    if not os.path.exists(out_dxf_path) or os.path.getsize(out_dxf_path) == 0:
        raise RuntimeError("Chuyển đổi DWG sang DXF thất bại qua accoreconsole!")
    return os.path.getsize(out_dxf_path)


def run_vision_detection(dxf_path, output_dir=None, expected_stairs=None):
    """
    Phân tích thực thể, render và nhận diện tường, cửa, bbox, vị trí.
    Xuất ảnh floorplan_annotated.png, floorplan_base.png, crop cửa, detection_result.json.
    """
    import cv2
    import ezdxf
    from ezdxf.bbox import extents
    from ezdxf.addons.drawing import Frontend, RenderContext
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    if output_dir is None:
        output_dir = DEFAULT_VISION_DIR
    os.makedirs(output_dir, exist_ok=True)

    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    bb = extents(msp)
    margin = 500.0
    min_x, max_x = bb.extmin.x - margin, bb.extmax.x + margin
    min_y, max_y = bb.extmin.y - margin, bb.extmax.y + margin
    cad_w, cad_h = max_x - min_x, max_y - min_y
    if cad_w <= 0 or cad_h <= 0:
        raise ValueError("Kích thước bản vẽ DXF không hợp lệ (chiều rộng hoặc chiều dài <= 0)")

    img_w = 4000
    img_h = max(600, int(img_w * (cad_h / cad_w)))
    dpi = 200

    fig = plt.figure(figsize=(img_w / dpi, img_h / dpi), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor("#1e1e1e")
    fig.patch.set_facecolor("#1e1e1e")

    ctx = RenderContext(doc)
    out = MatplotlibBackend(ax)
    Frontend(ctx, out).draw_layout(msp, finalize=False)
    ax.set_xlim(min_x, max_x)
    ax.set_ylim(min_y, max_y)
    ax.set_aspect("equal")
    ax.axis("off")

    clean_base = os.path.join(output_dir, "floorplan_base.png")
    fig.savefig(clean_base, dpi=dpi, facecolor="#1e1e1e")
    plt.close(fig)

    def cad_to_pixel(x, y):
        return int((x - min_x) / cad_w * img_w), int((max_y - y) / cad_h * img_h)

    def cad_bbox_to_pixel(bx1, by1, bx2, by2):
        px1, py1 = cad_to_pixel(bx1, by2)
        px2, py2 = cad_to_pixel(bx2, by1)
        return min(px1, px2), min(py1, py2), max(px1, px2), max(py1, py2)

    doors_raw = []
    walls_raw = []
    windows_raw = []
    columns_raw = []

    for e in msp:
        layer = e.dxf.layer.upper()
        etype = e.dxftype()
        try:
            ebb = extents([e])
        except Exception:
            continue

        c = ((ebb.extmin.x + ebb.extmax.x)/2, (ebb.extmin.y + ebb.extmax.y)/2)

        if any(k in layer for k in ["A-DOOR", "32-CUA", "CUA", "DOOR"]) and not any(k in layer for k in ["CUA SO", "CUA-SO"]):
            doors_raw.append({"entity": etype, "min": (ebb.extmin.x, ebb.extmin.y), "max": (ebb.extmax.x, ebb.extmax.y), "center": c})
        elif any(k in layer for k in ["CUA SO", "CUA-SO", "WINDOW", "GLAZ"]):
            windows_raw.append({"entity": etype, "min": (ebb.extmin.x, ebb.extmin.y), "max": (ebb.extmax.x, ebb.extmax.y), "center": c})
        elif any(k in layer for k in ["NET-02", "NET02", "NET03", "NET-03", "LAYERMANH"]) and etype in ["LINE", "LWPOLYLINE"]:
            dx = ebb.extmax.x - ebb.extmin.x
            dy = ebb.extmax.y - ebb.extmin.y
            L = max(dx, dy)
            D = min(dx, dy)
            if 800 <= L <= 3500 and D <= 350:
                windows_raw.append({"entity": etype, "min": (ebb.extmin.x, ebb.extmin.y), "max": (ebb.extmax.x, ebb.extmax.y), "center": c})
        elif any(k in layer for k in ["COT", "COLU"]):
            columns_raw.append({"entity": etype, "min": (ebb.extmin.x, ebb.extmin.y), "max": (ebb.extmax.x, ebb.extmax.y), "center": c})
        elif any(k in layer for k in ["TUONG", "A-WALL", "WALL", "S5", "NET03", "NET-02", "N THAY 0.25"]):
            dx = ebb.extmax.x - ebb.extmin.x
            dy = ebb.extmax.y - ebb.extmin.y
            length = max(dx, dy)
            if length > 250:
                walls_raw.append({"entity": etype, "min": (ebb.extmin.x, ebb.extmin.y), "max": (ebb.extmax.x, ebb.extmax.y), "center": c, "length": length, "orientation": "Horizontal" if dx > dy else "Vertical"})

    def cluster_items(items, max_d=1100, min_sz=400, max_sz=3000):
        clustered = []
        used = set()
        for i, it1 in enumerate(items):
            if i in used:
                continue
            cur = [it1]
            used.add(i)
            for j, it2 in enumerate(items):
                if j in used:
                    continue
                if np.hypot(it1["center"][0]-it2["center"][0], it1["center"][1]-it2["center"][1]) < max_d:
                    cur.append(it2)
                    used.add(j)
            bx1 = min(x["min"][0] for x in cur)
            by1 = min(x["min"][1] for x in cur)
            bx2 = max(x["max"][0] for x in cur)
            by2 = max(x["max"][1] for x in cur)
            w, h = bx2 - bx1, by2 - by1
            if min_sz <= max(w, h) <= max_sz:
                clustered.append({"min": (bx1, by1), "max": (bx2, by2), "center": ((bx1+bx2)/2, (by1+by2)/2), "width_mm": round(max(w, h), 1), "depth_mm": round(min(w, h), 1)})
        return clustered

    doors = cluster_items(doors_raw, max_d=1100, min_sz=400, max_sz=2500)
    doors.sort(key=lambda d: d["center"][0])
    
    # Gom cụm cửa sổ: Lọc không cho dải mỏng bị gộp nhầm thành thang
    def cluster_windows(items, max_d=1200, min_sz=800, max_sz=3500):
        clustered = []
        used = set()
        for i, it1 in enumerate(items):
            if i in used:
                continue
            cur = [it1]
            used.add(i)
            for j, it2 in enumerate(items):
                if j in used:
                    continue
                if np.hypot(it1["center"][0]-it2["center"][0], it1["center"][1]-it2["center"][1]) < max_d:
                    cur.append(it2)
                    used.add(j)
            bx1 = min(x["min"][0] for x in cur)
            by1 = min(x["min"][1] for x in cur)
            bx2 = max(x["max"][0] for x in cur)
            by2 = max(x["max"][1] for x in cur)
            w, h = bx2 - bx1, by2 - by1
            if min_sz <= max(w, h) <= max_sz and min(w, h) <= 450:
                clustered.append({"min": (bx1, by1), "max": (bx2, by2), "center": ((bx1+bx2)/2, (by1+by2)/2), "width_mm": round(max(w, h), 1), "depth_mm": round(min(w, h), 1)})
        return clustered

    windows = cluster_windows(windows_raw)
    columns = cluster_items(columns_raw, max_d=600, min_sz=100, max_sz=1500)
    major_walls = [w for w in walls_raw if w["length"] >= 800]

    # --- Nhận diện Cầu thang, Tam cấp, Ram dốc qua hình học bậc & lớp ---
    tread_candidates = []
    for e in msp:
        layer = e.dxf.layer.upper()
        # LOẠI TRỪ DỨT ĐIỂM: Các nét thuộc cửa sổ, tường, cột không bao giờ là bậc thang
        if any(k in layer for k in ["CUA SO", "CUA-SO", "WINDOW", "GLAZ", "TUONG", "A-WALL", "COT", "COLU"]):
            continue
        if e.dxftype() == 'LINE':
            p1 = (e.dxf.start.x, e.dxf.start.y)
            p2 = (e.dxf.end.x, e.dxf.end.y)
            length = np.hypot(p2[0]-p1[0], p2[1]-p1[1])
            angle = np.degrees(np.arctan2(p2[1]-p1[1], p2[0]-p1[0])) % 180
            if 800 <= length <= 2200 and (abs(angle-0) < 12 or abs(angle-180) < 12 or abs(angle-90) < 12):
                c = ((p1[0]+p2[0])/2, (p1[1]+p2[1])/2)
                tread_candidates.append({'p1': p1, 'p2': p2, 'len': length, 'center': c, 'angle': angle, 'layer': layer})

    raw_tread_clusters = []
    used_treads = set()
    for i, t1 in enumerate(tread_candidates):
        if i in used_treads:
            continue
        cur = [t1]
        used_treads.add(i)
        for j, t2 in enumerate(tread_candidates):
            if j in used_treads:
                continue
            if abs(t1['angle'] - t2['angle']) < 10 or abs(abs(t1['angle'] - t2['angle']) - 180) < 10:
                if np.hypot(t1['center'][0] - t2['center'][0], t1['center'][1] - t2['center'][1]) < 2200:
                    cur.append(t2)
                    used_treads.add(j)
        # Một vế thang chuẩn luôn có ít nhất 6-8 bậc song song (cửa sổ sọc ngang chỉ có 2-4 nét)
        if len(cur) >= 6:
            all_x = [p for t in cur for p in (t['p1'][0], t['p2'][0])]
            all_y = [p for t in cur for p in (t['p1'][1], t['p2'][1])]
            bx1, by1, bx2, by2 = min(all_x), min(all_y), max(all_x), max(all_y)
            raw_tread_clusters.append({'box': [bx1, by1, bx2, by2], 'count': len(cur)})

    # Gộp cụm bậc gần nhau thành buồng thang / sảnh tam cấp
    merged_treads = []
    used_mc = set()
    for i, c1 in enumerate(raw_tread_clusters):
        if i in used_mc:
            continue
        cur_box = list(c1['box'])
        cnt = c1['count']
        used_mc.add(i)
        for j, c2 in enumerate(raw_tread_clusters):
            if j in used_mc:
                continue
            b2 = c2['box']
            gap = 1200.0
            if (cur_box[0] - gap <= b2[2] and cur_box[2] + gap >= b2[0] and
                cur_box[1] - gap <= b2[3] and cur_box[3] + gap >= b2[1]):
                cur_box[0] = min(cur_box[0], b2[0])
                cur_box[1] = min(cur_box[1], b2[1])
                cur_box[2] = max(cur_box[2], b2[2])
                cur_box[3] = max(cur_box[3], b2[3])
                cnt += c2['count']
                used_mc.add(j)
        w = cur_box[2] - cur_box[0]
        h = cur_box[3] - cur_box[1]
        merged_treads.append({'box': cur_box, 'w': w, 'h': h, 'count': cnt})

    valid_stairs = []
    detected_tam_cap = []
    detected_ramps = []

    for m in merged_treads:
        w, h = m['w'], m['h']
        sz_min, sz_max = min(w, h), max(w, h)
        # Buồng thang bộ thực tế: BẮT BUỘC cả 2 chiều sz_min >= 1400mm và sz_max >= 2400mm
        # (Loại bỏ triệt để các dải sọc mỏng <= 400mm của cửa sổ/tường)
        if sz_min >= 1400 and sz_max >= 2400 and m['count'] >= 6:
            score = m['count'] * 10 + (w * h) / 100000.0
            m['score'] = score
            valid_stairs.append(m)
        # Bậc tam cấp sảnh (Chiều sâu <= 1400mm, bề rộng dài >= 800mm, ít nhất 3 bậc)
        elif sz_min <= 1400 and sz_max >= 800 and m['count'] >= 3:
            detected_tam_cap.append(m)

    # Sắp xếp các ứng viên buồng thang theo điểm tin cậy giảm dần
    valid_stairs.sort(key=lambda s: s.get('score', 0), reverse=True)

    # Áp dụng bộ lọc số lượng cầu thang người dùng nhập (expected_stairs)
    detected_stairs = []
    if expected_stairs is not None and str(expected_stairs).strip().lower() not in ('auto', 'all', ''):
        try:
            target_count = int(expected_stairs)
            if target_count > 0:
                detected_stairs = valid_stairs[:target_count]
            else:
                detected_stairs = [] # Người dùng nhập 0 -> Không có thang
        except (ValueError, TypeError):
            detected_stairs = valid_stairs
    else:
        detected_stairs = valid_stairs

    # Nhận diện Ram dốc giữa các bậc sảnh chính hoặc qua layer
    if len(detected_tam_cap) >= 2:
        tc_sorted = sorted(detected_tam_cap, key=lambda x: x['box'][0])
        tc_front = [tc for tc in tc_sorted if tc['box'][1] < min_y + cad_h * 0.4]
        if len(tc_front) >= 2:
            rx1 = tc_front[0]['box'][2]
            rx2 = tc_front[-1]['box'][0]
            if 1000 <= (rx2 - rx1) <= 12000:
                detected_ramps.append({
                    'box': [rx1, min(tc_front[0]['box'][1], tc_front[-1]['box'][1]) - 500.0,
                            rx2, max(tc_front[0]['box'][3], tc_front[-1]['box'][3]) + 500.0],
                    'w': rx2 - rx1,
                    'h': 1600.0,
                    'count': 1
                })

    vis_img = cv2.imread(clean_base)
    crops_dir = os.path.join(output_dir, "crops")
    os.makedirs(crops_dir, exist_ok=True)

    results = {
        "cad_file": dxf_path,
        "cad_extents_mm": {
            "width": round(cad_w, 1),
            "height": round(cad_h, 1),
            "min_x": round(min_x, 1),
            "max_x": round(max_x, 1),
            "min_y": round(min_y, 1),
            "max_y": round(max_y, 1)
        },
        "counts": {
            "doors": len(doors),
            "windows": len(windows),
            "columns": len(columns),
            "major_walls": len(major_walls),
            "stairs": len(detected_stairs),
            "tam_cap": len(detected_tam_cap),
            "ramps": len(detected_ramps)
        },
        "doors": [], "walls": [], "columns": [], "windows": [],
        "stairs": [], "tam_cap": [], "ramps": []
    }

    # Format Walls
    for i, w in enumerate(major_walls):
        px1, py1, px2, py2 = cad_bbox_to_pixel(*w["min"], *w["max"])
        results["walls"].append({
            "id": f"WALL_{i+1:03d}",
            "orientation": w["orientation"],
            "length_mm": round(w["length"], 1),
            "center_cad": [round(w["center"][0], 1), round(w["center"][1], 1)],
            "cad_box": [round(w["min"][0], 1), round(w["min"][1], 1), round(w["max"][0], 1), round(w["max"][1], 1)],
            "bbox_pixels": [px1, py1, px2, py2]
        })

    # Format Columns
    for i, col in enumerate(columns):
        px1, py1, px2, py2 = cad_bbox_to_pixel(*col["min"], *col["max"])
        results["columns"].append({
            "id": f"COL_{i+1:02d}",
            "dimension_mm": f"{col['width_mm']}x{col['depth_mm']}",
            "center_cad": [round(col["center"][0], 1), round(col["center"][1], 1)],
            "cad_box": [round(col["min"][0], 1), round(col["min"][1], 1), round(col["max"][0], 1), round(col["max"][1], 1)],
            "bbox_pixels": [px1, py1, px2, py2]
        })

    # Format Windows
    for i, win in enumerate(windows):
        px1, py1, px2, py2 = cad_bbox_to_pixel(*win["min"], *win["max"])
        results["windows"].append({
            "id": f"WIN_{i+1:02d}",
            "width_mm": win["width_mm"],
            "center_cad": [round(win["center"][0], 1), round(win["center"][1], 1)],
            "cad_box": [round(win["min"][0], 1), round(win["min"][1], 1), round(win["max"][0], 1), round(win["max"][1], 1)],
            "bbox_pixels": [px1, py1, px2, py2]
        })

    # Format Doors
    for i, d in enumerate(doors):
        d_id = f"DOOR_{i+1:02d}"
        px1, py1, px2, py2 = cad_bbox_to_pixel(*d["min"], *d["max"])
        px1, py1 = max(0, px1 - 6), max(0, py1 - 6)
        px2, py2 = min(img_w - 1, px2 + 6), min(img_h - 1, py2 + 6)

        results["doors"].append({
            "id": d_id,
            "type": "Cửa đi 2 cánh" if d["width_mm"] >= 1300 else "Cửa đi 1 cánh",
            "width_mm": d["width_mm"],
            "depth_mm": d["depth_mm"],
            "center_cad": [round(d["center"][0], 1), round(d["center"][1], 1)],
            "cad_box": [round(d["min"][0], 1), round(d["min"][1], 1), round(d["max"][0], 1), round(d["max"][1], 1)],
            "bbox_pixels": [px1, py1, px2, py2],
            "crop_url": f"/api/cad/vision-crop/{d_id}.png"
        })

    # Format Stairs
    for i, s in enumerate(detected_stairs):
        s_id = f"STAIR_{i+1:02d}"
        px1, py1, px2, py2 = cad_bbox_to_pixel(s["box"][0], s["box"][1], s["box"][2], s["box"][3])
        results["stairs"].append({
            "id": s_id,
            "name": f"Cầu thang bộ #{i+1}",
            "type": "Cầu thang",
            "width_mm": round(s["w"], 1),
            "depth_mm": round(s["h"], 1),
            "center_cad": [round((s["box"][0] + s["box"][2])/2, 1), round((s["box"][1] + s["box"][3])/2, 1)],
            "cad_box": [round(s["box"][0], 1), round(s["box"][1], 1), round(s["box"][2], 1), round(s["box"][3], 1)],
            "bbox_pixels": [px1, py1, px2, py2]
        })

    # Format Tam Cấp
    for i, tc in enumerate(detected_tam_cap):
        tc_id = f"STEP_{i+1:02d}"
        px1, py1, px2, py2 = cad_bbox_to_pixel(tc["box"][0], tc["box"][1], tc["box"][2], tc["box"][3])
        results["tam_cap"].append({
            "id": tc_id,
            "name": f"Tam cấp sảnh #{i+1}",
            "type": "Tam cấp",
            "width_mm": round(tc["w"], 1),
            "depth_mm": round(tc["h"], 1),
            "center_cad": [round((tc["box"][0] + tc["box"][2])/2, 1), round((tc["box"][1] + tc["box"][3])/2, 1)],
            "cad_box": [round(tc["box"][0], 1), round(tc["box"][1], 1), round(tc["box"][2], 1), round(tc["box"][3], 1)],
            "bbox_pixels": [px1, py1, px2, py2]
        })

    # Format Ramps
    for i, r in enumerate(detected_ramps):
        r_id = f"RAMP_{i+1:02d}"
        px1, py1, px2, py2 = cad_bbox_to_pixel(r["box"][0], r["box"][1], r["box"][2], r["box"][3])
        results["ramps"].append({
            "id": r_id,
            "name": f"Ram dốc #{i+1}",
            "type": "Ram dốc",
            "width_mm": round(r["w"], 1),
            "depth_mm": round(r["h"], 1),
            "center_cad": [round((r["box"][0] + r["box"][2])/2, 1), round((r["box"][1] + r["box"][3])/2, 1)],
            "cad_box": [round(r["box"][0], 1), round(r["box"][1], 1), round(r["box"][2], 1), round(r["box"][3], 1)],
            "bbox_pixels": [px1, py1, px2, py2]
        })

    # Save door crops
    for d in results["doors"]:
        px1, py1, px2, py2 = d["bbox_pixels"]
        crop = vis_img[max(0, py1-40):min(img_h-1, py2+40), max(0, px1-40):min(img_w-1, px2+40)]
        crop_file = os.path.join(crops_dir, f"{d['id']}.png")
        if crop.size > 0:
            cv2.imwrite(crop_file, crop)

    # Render annotations
    draw_annotations_on_image(vis_img, results, img_w, img_h)

    annotated_path = os.path.join(output_dir, "floorplan_annotated.png")
    cv2.imwrite(annotated_path, vis_img)
    json_path = os.path.join(output_dir, "detection_result.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    return results


def draw_annotations_on_image(vis_img, results, img_w, img_h):
    """Vẽ bounding box và nhãn phân loại lên ảnh với các màu chuẩn nhận diện."""
    import cv2

    # 1. Tường (Đỏ nét mảnh)
    for w in results.get("walls", []):
        bp = w.get("bbox_pixels")
        if bp and len(bp) == 4:
            px1, py1, px2, py2 = bp
            cv2.rectangle(vis_img, (px1, py1), (max(px2, px1+2), max(py2, py1+2)), (0, 0, 255), 1)

    # 2. Cột (Vàng)
    for col in results.get("columns", []):
        bp = col.get("bbox_pixels")
        if bp and len(bp) == 4:
            px1, py1, px2, py2 = bp
            cv2.rectangle(vis_img, (px1, py1), (px2, py2), (0, 215, 255), 2)

    # 3. Cửa sổ (Cyan)
    for win in results.get("windows", []):
        bp = win.get("bbox_pixels")
        if bp and len(bp) == 4:
            px1, py1, px2, py2 = bp
            cv2.rectangle(vis_img, (px1, py1), (px2, py2), (255, 255, 0), 2)

    # 4. Cửa đi (Xanh lá)
    for d in results.get("doors", []):
        bp = d.get("bbox_pixels")
        if bp and len(bp) == 4:
            px1, py1, px2, py2 = bp
            cv2.rectangle(vis_img, (px1, py1), (px2, py2), (0, 255, 0), 3)
            lbl = f"{d.get('id', 'DOOR')} ({int(d.get('width_mm', 0))}mm)"
            (tw, th), _ = cv2.getTextSize(lbl, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(vis_img, (px1, max(0, py1 - th - 8)), (min(img_w - 1, px1 + tw + 10), py1), (0, 180, 0), -1)
            cv2.putText(vis_img, lbl, (px1 + 5, py1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2, cv2.LINE_AA)

    # 5. Tam cấp (Tím #a855f7)
    for tc in results.get("tam_cap", []):
        bp = tc.get("bbox_pixels")
        if bp and len(bp) == 4:
            px1, py1, px2, py2 = bp
            cv2.rectangle(vis_img, (px1, py1), (px2, py2), (247, 85, 168), 3)
            lbl = f"{tc.get('id', 'STEP')} (Tam cap {int(tc.get('width_mm', 0))}mm)"
            (tw, th), _ = cv2.getTextSize(lbl, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(vis_img, (px1, max(0, py1 - th - 8)), (min(img_w - 1, px1 + tw + 10), py1), (247, 85, 168), -1)
            cv2.putText(vis_img, lbl, (px1 + 5, py1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2, cv2.LINE_AA)

    # 6. Ram dốc (Hồng đậm #f43f5e)
    for r in results.get("ramps", []):
        bp = r.get("bbox_pixels")
        if bp and len(bp) == 4:
            px1, py1, px2, py2 = bp
            cv2.rectangle(vis_img, (px1, py1), (px2, py2), (94, 63, 244), 3)
            lbl = f"{r.get('id', 'RAMP')} (Ram doc {int(r.get('width_mm', 0))}mm)"
            (tw, th), _ = cv2.getTextSize(lbl, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(vis_img, (px1, max(0, py1 - th - 8)), (min(img_w - 1, px1 + tw + 10), py1), (94, 63, 244), -1)
            cv2.putText(vis_img, lbl, (px1 + 5, py1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)

    # 7. Cầu thang bộ (Cam vàng #f59e0b)
    for s in results.get("stairs", []):
        bp = s.get("bbox_pixels")
        if bp and len(bp) == 4:
            px1, py1, px2, py2 = bp
            cv2.rectangle(vis_img, (px1, py1), (px2, py2), (11, 158, 245), 4)
            lbl = f"{s.get('id', 'STAIR')} (Thang {int(s.get('width_mm', 0))}x{int(s.get('depth_mm', 0))}mm)"
            (tw, th), _ = cv2.getTextSize(lbl, cv2.FONT_HERSHEY_SIMPLEX, 0.65, 2)
            cv2.rectangle(vis_img, (px1, max(0, py1 - th - 8)), (min(img_w - 1, px1 + tw + 10), py1), (11, 158, 245), -1)
            cv2.putText(vis_img, lbl, (px1 + 5, py1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 2, cv2.LINE_AA)


def redraw_annotated_image(results, output_dir=None):
    """Vẽ lại ảnh floorplan_annotated.png từ kết quả detection hiện tại."""
    import cv2
    if output_dir is None:
        output_dir = DEFAULT_VISION_DIR
    clean_base = os.path.join(output_dir, "floorplan_base.png")
    if not os.path.exists(clean_base):
        return None
    vis_img = cv2.imread(clean_base)
    img_h, img_w = vis_img.shape[:2]
    draw_annotations_on_image(vis_img, results, img_w, img_h)
    annotated_path = os.path.join(output_dir, "floorplan_annotated.png")
    cv2.imwrite(annotated_path, vis_img)
    return annotated_path


def update_vision_annotations(updated_data, output_dir=None):
    """
    Cập nhật danh sách bounding box (Thang, Tam cấp, Ram dốc, Cửa, Cột,...) do user chỉ định lại từ Canvas.
    Ghi đè detection_result.json và vẽ lại floorplan_annotated.png.
    """
    import cv2
    if output_dir is None:
        output_dir = DEFAULT_VISION_DIR
    json_path = os.path.join(output_dir, "detection_result.json")
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            results = json.load(f)
    else:
        results = {"counts": {}, "doors": [], "windows": [], "columns": [], "walls": [], "stairs": [], "tam_cap": [], "ramps": []}

    extents = results.get("cad_extents_mm", {})
    cad_w = extents.get("width", 40000.0)
    cad_h = extents.get("height", 25000.0)
    min_x = extents.get("min_x", 0.0)
    max_y = extents.get("max_y", 0.0)
    clean_base = os.path.join(output_dir, "floorplan_base.png")
    if os.path.exists(clean_base):
        base_img = cv2.imread(clean_base)
        img_h, img_w = base_img.shape[:2]
    else:
        img_w, img_h = 4000, 2320

    # Nếu truyền danh sách 'annotations' phẳng từ Canvas:
    if "annotations" in updated_data and isinstance(updated_data["annotations"], list):
        new_stairs = []
        new_tam_cap = []
        new_ramps = []
        new_doors = []
        new_windows = []
        new_columns = []
        new_walls = []

        for item in updated_data["annotations"]:
            cat = (item.get("category") or item.get("type") or "").lower()
            bp = item.get("bbox_pixels")
            if bp and len(bp) == 4 and not item.get("cad_box"):
                px1, py1, px2, py2 = bp
                cx1 = round(min_x + (px1 / img_w) * cad_w, 1)
                cx2 = round(min_x + (px2 / img_w) * cad_w, 1)
                cy1 = round(max_y - (py2 / img_h) * cad_h, 1)
                cy2 = round(max_y - (py1 / img_h) * cad_h, 1)
                item["cad_box"] = [min(cx1, cx2), min(cy1, cy2), max(cx1, cx2), max(cy1, cy2)]
                item["center_cad"] = [round((cx1 + cx2)/2, 1), round((cy1 + cy2)/2, 1)]
                item["width_mm"] = round(abs(cx2 - cx1), 1)
                item["depth_mm"] = round(abs(cy2 - cy1), 1)

            if "thang" in cat or "stair" in cat:
                new_stairs.append(item)
            elif "tam_cap" in cat or "tam cap" in cat or "step" in cat:
                new_tam_cap.append(item)
            elif "ramp" in cat or "doc" in cat or "dốc" in cat:
                new_ramps.append(item)
            elif "door" in cat or "cua di" in cat or "cửa đi" in cat:
                new_doors.append(item)
            elif "window" in cat or "cua so" in cat or "cửa sổ" in cat:
                new_windows.append(item)
            elif "col" in cat or "cot" in cat or "cột" in cat:
                new_columns.append(item)
            elif "wall" in cat or "tuong" in cat or "tường" in cat:
                new_walls.append(item)

        results["stairs"] = new_stairs
        results["tam_cap"] = new_tam_cap
        results["ramps"] = new_ramps
        results["doors"] = new_doors
        results["windows"] = new_windows
        results["columns"] = new_columns
        results["walls"] = new_walls

    else:
        for k in ["stairs", "tam_cap", "ramps", "doors", "windows", "columns", "walls"]:
            if k in updated_data:
                results[k] = updated_data[k]

    results["counts"] = {
        "doors": len(results.get("doors", [])),
        "windows": len(results.get("windows", [])),
        "columns": len(results.get("columns", [])),
        "major_walls": len(results.get("walls", [])),
        "stairs": len(results.get("stairs", [])),
        "tam_cap": len(results.get("tam_cap", [])),
        "ramps": len(results.get("ramps", []))
    }

    redraw_annotated_image(results, output_dir)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    return {"status": "success", "counts": results["counts"], "vision": results}


# ==============================================================================
# 3D Wavefront OBJ Mesh Generator
# ==============================================================================

class ObjMeshBuilder:
    def __init__(self, name, scale=0.001, offset=(0, 0, 0)):
        self.name = name
        self.scale = scale
        self.ox, self.oy, self.oz = offset
        self.vertices = []
        self.faces = []
        self.material = None

    def transform(self, x, y, z):
        tx = (x - self.ox) * self.scale
        ty = (y - self.oy) * self.scale
        tz = (z - self.oz) * self.scale
        return tx, ty, tz

    def add_quad(self, p1, p2, p3, p4, double_sided=True):
        idx = len(self.vertices) + 1
        self.vertices.append(self.transform(*p1))
        self.vertices.append(self.transform(*p2))
        self.vertices.append(self.transform(*p3))
        self.vertices.append(self.transform(*p4))
        self.faces.append((idx, idx+1, idx+2, idx+3))
        if double_sided:
            self.faces.append((idx+3, idx+2, idx+1, idx))

    def add_box(self, x1, y1, z1, x2, y2, z2):
        self.add_quad((x1, y1, z1), (x2, y1, z1), (x2, y2, z1), (x1, y2, z1))
        self.add_quad((x1, y1, z2), (x2, y1, z2), (x2, y2, z2), (x1, y2, z2))
        self.add_quad((x1, y1, z1), (x2, y1, z1), (x2, y1, z2), (x1, y1, z2))
        self.add_quad((x2, y1, z1), (x2, y2, z1), (x2, y2, z2), (x2, y1, z2))
        self.add_quad((x2, y2, z1), (x1, y2, z1), (x1, y2, z2), (x2, y2, z2))
        self.add_quad((x1, y2, z1), (x1, y1, z1), (x1, y1, z2), (x1, y2, z2))

    def add_vertical_wall(self, p1_2d, p2_2d, z_bottom, z_top, double_sided=True):
        v1 = (p1_2d[0], p1_2d[1], z_bottom)
        v2 = (p2_2d[0], p2_2d[1], z_bottom)
        v3 = (p2_2d[0], p2_2d[1], z_top)
        v4 = (p1_2d[0], p1_2d[1], z_top)
        self.add_quad(v1, v2, v3, v4, double_sided=double_sided)

    def add_horizontal_quad(self, p1_2d, p2_2d, p3_2d, p4_2d, z, double_sided=True):
        v1 = (p1_2d[0], p1_2d[1], z)
        v2 = (p2_2d[0], p2_2d[1], z)
        v3 = (p3_2d[0], p3_2d[1], z)
        v4 = (p4_2d[0], p4_2d[1], z)
        self.add_quad(v1, v2, v3, v4, double_sided=double_sided)

    def add_thickened_ribbon(self, p1_2d, p2_2d, z, width=40.0):
        x1, y1 = p1_2d
        x2, y2 = p2_2d
        dx, dy = x2 - x1, y2 - y1
        L = np.hypot(dx, dy)
        if L < 1e-4:
            return
        nx, ny = -dy / L * (width/2), dx / L * (width/2)
        v1 = (x1 - nx, y1 - ny, z)
        v2 = (x2 - nx, y2 - ny, z)
        v3 = (x2 + nx, y2 + ny, z)
        v4 = (x1 + nx, y1 + ny, z)
        self.add_quad(v1, v2, v3, v4, double_sided=True)

    def write_obj(self, filepath, mtl_filename=None):
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("# Wavefront OBJ File\n")
            f.write(f"# Object Name: {self.name}\n")
            f.write(f"# Scale: 1 unit = {'1 meter' if self.scale == 0.001 else '1 mm'}\n")
            if mtl_filename:
                f.write(f"mtllib {mtl_filename}\n")
            f.write(f"o {self.name}\n")
            if self.material:
                f.write(f"usemtl {self.material}\n")
            for v in self.vertices:
                f.write(f"v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n")
            for face in self.faces:
                f.write(f"f {' '.join(str(idx) for idx in face)}\n")


def write_mtl(filepath):
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# Materials for Architectural Floorplan OBJ Models\n\n")
        f.write("newmtl mat_wall\n")
        f.write("Kd 0.85 0.85 0.85\nKa 0.25 0.25 0.25\nKs 0.1 0.1 0.1\nNs 10.0\nd 1.0\n\n")
        f.write("newmtl mat_door\n")
        f.write("Kd 0.65 0.35 0.15\nKa 0.2 0.1 0.05\nKs 0.2 0.2 0.2\nNs 20.0\nd 1.0\n\n")
        f.write("newmtl mat_window\n")
        f.write("Kd 0.35 0.75 0.95\nKa 0.1 0.2 0.3\nKs 0.8 0.8 0.8\nNs 50.0\nd 0.65\n\n")
        f.write("newmtl mat_stair\n")
        f.write("Kd 0.85 0.55 0.20\nKa 0.25 0.15 0.05\nKs 0.3 0.3 0.3\nNs 20.0\nd 1.0\n\n")


def generate_3d_obj_models(dxf_path, output_dir=None, expected_stairs=None):
    """
    Tạo các file Wavefront OBJ cho Tường, Cửa đi, Cửa sổ, Cầu thang, Ram dốc và Toàn bộ nhà.
    Xuất cả hệ mét (scale=0.001) và hệ mm (scale=1.0).
    """
    import ezdxf
    from ezdxf.bbox import extents
    import trimesh

    if output_dir is None:
        output_dir = DEFAULT_MODELS_DIR
    out_m = os.path.join(output_dir, "meters")
    out_mm = os.path.join(output_dir, "cad_mm")
    os.makedirs(out_m, exist_ok=True)
    os.makedirs(out_mm, exist_ok=True)

    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    bb = extents(msp)
    min_x = bb.extmin.x
    min_y = bb.extmin.y
    max_x = bb.extmax.x
    max_y = bb.extmax.y

    # Default building coordinates or dynamic bounding box
    if 400000 <= min_x <= 460000 and -1500000 <= min_y <= -1460000:
        BUILDING_X_MIN = 407000.0
        BUILDING_X_MAX = 454000.0
        BUILDING_Y_MIN = -1493000.0
        BUILDING_Y_MAX = -1473000.0
        has_special_zones = True
    else:
        BUILDING_X_MIN = min_x
        BUILDING_X_MAX = max_x
        BUILDING_Y_MIN = min_y
        BUILDING_Y_MAX = max_y
        has_special_zones = False

    origin_x = BUILDING_X_MIN
    origin_y = BUILDING_Y_MIN

    stair_cores = []
    tam_cap_zones = []
    ramp_zones = []

    # Ưu tiên nạp danh sách buồng thang, tam cấp, ram dốc từ kết quả Vision / Canvas do user chỉ định
    v_json_path = os.path.join(DEFAULT_VISION_DIR, "detection_result.json")
    v_data = {}
    if os.path.exists(v_json_path):
        try:
            with open(v_json_path, "r", encoding="utf-8") as f:
                v_data = json.load(f)
        except Exception:
            pass

    loaded_stairs = v_data.get("stairs", [])
    if expected_stairs is not None and str(expected_stairs).strip().lower() not in ('auto', 'all', ''):
        try:
            target_count = int(expected_stairs)
            if target_count <= 0:
                loaded_stairs = []
            else:
                loaded_stairs = loaded_stairs[:target_count]
        except (ValueError, TypeError):
            pass
    loaded_tamcap = v_data.get("tam_cap", [])
    loaded_ramps = v_data.get("ramps", [])

    if loaded_stairs or loaded_tamcap or loaded_ramps:
        has_special_zones = True
        for i, s in enumerate(loaded_stairs):
            box = s.get("cad_box")
            if not box and "center_cad" in s:
                cx, cy = s["center_cad"]
                w, d = s.get("width_mm", 3000), s.get("depth_mm", 3000)
                box = [cx - w/2, cy - d/2, cx + w/2, cy + d/2]
            if box:
                bx1, by1, bx2, by2 = box
                sw = bx2 - bx1
                sh = by2 - by1
                mid_x = (bx1 + bx2) / 2
                gap = min(150.0, sw * 0.05)
                stair_cores.append({
                    "name": s.get("id", f"Stair_{i+1:02d}"),
                    "box": (bx1, by1, bx2, by2),
                    "x_left_min": bx1 + 100.0, "x_left_max": mid_x - gap/2,
                    "x_right_min": mid_x + gap/2, "x_right_max": bx2 - 100.0,
                    "x_shaft_left": bx1, "x_shaft_right": bx2,
                    "y_bottom": by1 + sh * 0.15, "y_top": by1 + sh * 0.75,
                    "y_landing_top": by2, "y_shaft_bottom": by1
                })

        for i, tc in enumerate(loaded_tamcap):
            box = tc.get("cad_box")
            if not box and "center_cad" in tc:
                cx, cy = tc["center_cad"]
                w, d = tc.get("width_mm", 2000), tc.get("depth_mm", 600)
                box = [cx - w/2, cy - d/2, cx + w/2, cy + d/2]
            if box:
                bx1, by1, bx2, by2 = box
                w = bx2 - bx1
                h = by2 - by1
                if w >= h:
                    steps_y = list(np.linspace(by1, by2, 4))
                    tam_cap_zones.append({
                        "name": tc.get("id", f"TamCap_{i+1:02d}"),
                        "box": (bx1, by1, bx2, by2),
                        "type": "stepped_y",
                        "y_steps": steps_y,
                        "x_min": bx1, "x_max": bx2,
                        "direction": "-y"
                    })
                else:
                    steps_x = list(np.linspace(bx1, bx2, 4))
                    tam_cap_zones.append({
                        "name": tc.get("id", f"TamCap_{i+1:02d}"),
                        "box": (bx1, by1, bx2, by2),
                        "type": "stepped_x",
                        "x_steps": steps_x,
                        "y_min": by1, "y_max": by2,
                        "direction": "+x"
                    })

        for i, r in enumerate(loaded_ramps):
            box = r.get("cad_box")
            if not box and "center_cad" in r:
                cx, cy = r["center_cad"]
                w, d = r.get("width_mm", 2000), r.get("depth_mm", 5000)
                box = [cx - w/2, cy - d/2, cx + w/2, cy + d/2]
            if box:
                bx1, by1, bx2, by2 = box
                ramp_zones.append({
                    "name": r.get("id", f"Ramp_{i+1:02d}"),
                    "box": (bx1, by1, bx2, by2),
                    "x_left": bx1, "x_right": bx2,
                    "y_start": by1, "y_end": by2,
                    "z_start": 0.0, "z_end": 600.0,
                    "curb_width": 100.0, "curb_height": 150.0
                })
    elif has_special_zones:
        # Fallback mẫu nếu tọa độ khớp bản vẽ demo cũ
        stair_cores = [
            {
                "name": "Stair_West",
                "box": (418000.0, -1482800.0, 422500.0, -1475300.0),
                "x_left_min": 418425.4, "x_left_max": 419800.4,
                "x_right_min": 420550.4, "x_right_max": 421925.4,
                "x_shaft_left": 418425.4, "x_shaft_right": 422125.4,
                "y_bottom": -1480300.0, "y_top": -1477250.0,
                "y_landing_top": -1475380.0, "y_shaft_bottom": -1482680.0
            },
            {
                "name": "Stair_East",
                "box": (443200.0, -1482800.0, 447700.0, -1475300.0),
                "x_left_min": 443625.4, "x_left_max": 445000.4,
                "x_right_min": 445750.4, "x_right_max": 447125.4,
                "x_shaft_left": 443625.4, "x_shaft_right": 447325.4,
                "y_bottom": -1480300.0, "y_top": -1477250.0,
                "y_landing_top": -1475380.0, "y_shaft_bottom": -1482680.0
            }
        ]
        tam_cap_zones = [
            {
                "name": "Tam_Cap_Tien_Sanh_Tay",
                "box": (408500.0, -1486000.0, 410200.0, -1481500.0),
                "type": "stepped_x",
                "x_steps": [408749.5, 409049.5, 409349.5, 409649.5, 409949.5],
                "y_min": -1485578.5, "y_max": -1481978.5,
                "direction": "+x"
            },
            {
                "name": "Tam_Cap_Phu_Tay",
                "box": (410000.0, -1481500.0, 414000.0, -1480000.0),
                "type": "stepped_y",
                "y_steps": [-1480378.5, -1480678.5, -1480978.5, -1481278.5],
                "x_min": 410225.4, "x_max": 413725.4,
                "direction": "-y"
            },
            {
                "name": "Tam_Cap_Sanh_Dong",
                "box": (452000.0, -1485200.0, 454000.0, -1482400.0),
                "type": "stepped_x",
                "x_steps": [453525.4, 453225.4, 452925.4, 452625.4, 452325.4],
                "y_min": -1484878.5, "y_max": -1482678.5,
                "direction": "-x"
            }
        ]
        ramp_zones = [
            {
                "name": "Ramp_Tien_Sanh_Tay",
                "box": (409500.0, -1491500.0, 414500.0, -1485500.0),
                "x_left": 410225.4, "x_right": 413725.4,
                "y_start": -1491278.5, "y_end": -1485678.5,
                "z_start": 0.0, "z_end": 600.0,
                "curb_width": 100.0, "curb_height": 150.0
            }
        ]

    def in_zone(zones, x, y):
        for z in zones:
            bx1, by1, bx2, by2 = z["box"]
            if bx1 <= x <= bx2 and by1 <= y <= by2:
                return z
        return None

    def is_valid_segment(p1, p2):
        return (BUILDING_X_MIN <= p1[0] <= BUILDING_X_MAX and
                BUILDING_Y_MIN <= p1[1] <= BUILDING_Y_MAX and
                BUILDING_X_MIN <= p2[0] <= BUILDING_X_MAX and
                BUILDING_Y_MIN <= p2[1] <= BUILDING_Y_MAX)

    def extract_segments(e):
        t = e.dxftype()
        raw_segs = []
        if t == "LINE":
            raw_segs.append(((e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)))
        elif t == "LWPOLYLINE":
            pts = list(e.get_points())
            closed = e.closed
            for i in range(len(pts) - 1):
                raw_segs.append(((pts[i][0], pts[i][1]), (pts[i+1][0], pts[i+1][1])))
            if closed and len(pts) > 2:
                raw_segs.append(((pts[-1][0], pts[-1][1]), (pts[0][0], pts[0][1])))
        elif t == "ARC":
            c = (e.dxf.center.x, e.dxf.center.y)
            r = e.dxf.radius
            sa = np.radians(e.dxf.start_angle)
            ea = np.radians(e.dxf.end_angle)
            if ea < sa:
                ea += 2 * np.pi
            steps = max(12, int(np.degrees(ea - sa) / 8))
            angles = np.linspace(sa, ea, steps + 1)
            arc_pts = [(c[0] + r * np.cos(a), c[1] + r * np.sin(a)) for a in angles]
            for i in range(len(arc_pts) - 1):
                raw_segs.append((arc_pts[i], arc_pts[i+1]))
        elif t == "CIRCLE":
            c = (e.dxf.center.x, e.dxf.center.y)
            r = e.dxf.radius
            angles = np.linspace(0, 2*np.pi, 24, endpoint=False)
            circ_pts = [(c[0] + r * np.cos(a), c[1] + r * np.sin(a)) for a in angles]
            for i in range(len(circ_pts)):
                raw_segs.append((circ_pts[i], circ_pts[(i+1)%len(circ_pts)]))
        elif t == "INSERT":
            try:
                for sub_e in e.virtual_entities():
                    raw_segs.extend(extract_segments(sub_e))
            except Exception:
                pass
        return [s for s in raw_segs if is_valid_segment(s[0], s[1])]

    wall_segments = []
    column_segments = []
    door_segments = []
    door_arcs = []
    window_segments = []

    for e in msp:
        layer = e.dxf.layer.upper()
        try:
            ebb = extents([e])
            cx = (ebb.extmin.x + ebb.extmax.x) / 2
            cy = (ebb.extmin.y + ebb.extmax.y) / 2
        except Exception:
            continue

        if not (BUILDING_X_MIN <= cx <= BUILDING_X_MAX and BUILDING_Y_MIN <= cy <= BUILDING_Y_MAX):
            continue

        if has_special_zones and (in_zone(stair_cores, cx, cy) or in_zone(tam_cap_zones, cx, cy) or in_zone(ramp_zones, cx, cy)):
            continue

        if any(k in layer for k in ["A-DOOR", "32-CUA", "CUA"]) and not any(k in layer for k in ["CUA SO", "CUA-SO"]):
            if e.dxftype() == "ARC":
                door_arcs.extend(extract_segments(e))
            else:
                door_segments.extend(extract_segments(e))
        elif any(k in layer for k in ["CUA SO", "CUA-SO", "WINDOW"]):
            window_segments.extend(extract_segments(e))
        elif any(k in layer for k in ["COT", "COLU"]):
            column_segments.extend(extract_segments(e))
        elif any(k in layer for k in ["TUONG", "A-WALL", "WALL", "S5", "NET03", "NET-02", "N THAY 0.25", "LAYERMANH"]):
            wall_segments.extend(extract_segments(e))

    def build_wall_mesh(scale, offset):
        mesh = ObjMeshBuilder("Wall", scale=scale, offset=offset)
        mesh.material = "mat_wall"
        wall_h = 3000.0
        for p1, p2 in wall_segments:
            mesh.add_vertical_wall(p1, p2, 0.0, wall_h)
        for p1, p2 in column_segments:
            mesh.add_vertical_wall(p1, p2, 0.0, wall_h)
        return mesh

    def build_door_mesh(scale, offset):
        mesh = ObjMeshBuilder("Door", scale=scale, offset=offset)
        mesh.material = "mat_door"
        door_h = 2100.0
        wall_h = 3000.0
        for p1, p2 in door_segments:
            mesh.add_vertical_wall(p1, p2, 0.0, door_h)
            mesh.add_vertical_wall(p1, p2, door_h, wall_h)
        for p1, p2 in door_arcs:
            mesh.add_thickened_ribbon(p1, p2, z=15.0, width=30.0)
        return mesh

    def build_window_mesh(scale, offset):
        mesh = ObjMeshBuilder("Window", scale=scale, offset=offset)
        mesh.material = "mat_window"
        sill_h = 900.0
        head_h = 2200.0
        wall_h = 3000.0
        for p1, p2 in window_segments:
            mesh.add_vertical_wall(p1, p2, 0.0, sill_h)
            mesh.add_vertical_wall(p1, p2, sill_h, head_h)
            mesh.add_vertical_wall(p1, p2, head_h, wall_h)
        return mesh

    def add_ramp_to_mesh(mesh, r):
        x_left = r["x_left"]
        x_right = r["x_right"]
        y_start = r["y_start"]
        y_end = r["y_end"]
        z_start = r["z_start"]
        z_end = r["z_end"]
        curb_w = r["curb_width"]
        curb_h = r["curb_height"]

        mesh.add_quad((x_left, y_start, z_start), (x_right, y_start, z_start), (x_right, y_end, z_end), (x_left, y_end, z_end), double_sided=True)
        mesh.add_quad((x_left, y_start, 0.0), (x_left, y_end, 0.0), (x_left, y_end, z_end), (x_left, y_start, z_start), double_sided=True)
        mesh.add_quad((x_right, y_start, 0.0), (x_right, y_end, 0.0), (x_right, y_end, z_end), (x_right, y_start, z_start), double_sided=True)
        mesh.add_quad((x_left, y_end, 0.0), (x_right, y_end, 0.0), (x_right, y_end, z_end), (x_left, y_end, z_end), double_sided=True)

        xl_out = x_left - curb_w
        mesh.add_quad((xl_out, y_start, z_start + curb_h), (x_left, y_start, z_start + curb_h), (x_left, y_end, z_end + curb_h), (xl_out, y_end, z_end + curb_h), double_sided=True)
        mesh.add_quad((xl_out, y_start, 0.0), (xl_out, y_end, 0.0), (xl_out, y_end, z_end + curb_h), (xl_out, y_start, z_start + curb_h), double_sided=True)
        mesh.add_quad((x_left, y_start, z_start), (x_left, y_end, z_end), (x_left, y_end, z_end + curb_h), (x_left, y_start, z_start + curb_h), double_sided=True)
        mesh.add_quad((xl_out, y_start, 0.0), (x_left, y_start, 0.0), (x_left, y_start, z_start + curb_h), (xl_out, y_start, z_start + curb_h), double_sided=True)
        mesh.add_quad((xl_out, y_end, 0.0), (x_left, y_end, 0.0), (x_left, y_end, z_end + curb_h), (xl_out, y_end, z_end + curb_h), double_sided=True)

        xr_out = x_right + curb_w
        mesh.add_quad((x_right, y_start, z_start + curb_h), (xr_out, y_start, z_start + curb_h), (xr_out, y_end, z_end + curb_h), (x_right, y_end, z_end + curb_h), double_sided=True)
        mesh.add_quad((xr_out, y_start, 0.0), (xr_out, y_end, 0.0), (xr_out, y_end, z_end + curb_h), (xr_out, y_start, z_start + curb_h), double_sided=True)
        mesh.add_quad((x_right, y_start, z_start), (x_right, y_end, z_end), (x_right, y_end, z_end + curb_h), (x_right, y_start, z_start + curb_h), double_sided=True)
        mesh.add_quad((x_right, y_start, 0.0), (xr_out, y_start, 0.0), (xr_out, y_start, z_start + curb_h), (x_right, y_start, z_start + curb_h), double_sided=True)
        mesh.add_quad((x_right, y_end, 0.0), (xr_out, y_end, 0.0), (xr_out, y_end, z_end + curb_h), (x_right, y_end, z_end + curb_h), double_sided=True)

    def build_stair_mesh(scale, offset):
        mesh = ObjMeshBuilder("Stair", scale=scale, offset=offset)
        mesh.material = "mat_stair"

        num_steps = 11
        flight1_h = 1500.0
        flight2_h = 3000.0
        dz = flight1_h / num_steps

        for sc in stair_cores:
            x_left = sc["x_shaft_left"]
            x_right = sc["x_shaft_right"]
            y_bottom = sc["y_shaft_bottom"]
            y_top = sc["y_landing_top"]

            mesh.add_vertical_wall((x_left, y_bottom), (x_left, y_top), 0.0, 3000.0)
            mesh.add_vertical_wall((x_right, y_bottom), (x_right, y_top), 0.0, 3000.0)
            mesh.add_vertical_wall((x_left, y_top), (x_right, y_top), 0.0, 3000.0)

            mesh.add_horizontal_quad((x_left, y_bottom), (x_right, y_bottom), (x_right, sc["y_bottom"]), (x_left, sc["y_bottom"]), z=0.0)

            y_l_start = sc["y_top"]
            y_l_end = sc["y_landing_top"]
            mesh.add_horizontal_quad((x_left, y_l_start), (x_right, y_l_start), (x_right, y_l_end), (x_left, y_l_end), z=flight1_h)
            mesh.add_vertical_wall((x_left, y_l_start), (x_right, y_l_start), flight1_h - 150.0, flight1_h)

            xl1 = sc["x_left_min"]
            xl2 = sc["x_left_max"]
            y_step_pitch = (sc["y_top"] - sc["y_bottom"]) / num_steps

            for i in range(num_steps):
                y_s = sc["y_bottom"] + i * y_step_pitch
                y_e = sc["y_bottom"] + (i + 1) * y_step_pitch
                z_s = i * dz
                z_e = (i + 1) * dz
                mesh.add_vertical_wall((xl1, y_s), (xl2, y_s), z_s, z_e)
                mesh.add_horizontal_quad((xl1, y_s), (xl2, y_s), (xl2, y_e), (xl1, y_e), z=z_e)

            mesh.add_vertical_wall((xl2, sc["y_bottom"]), (xl2, sc["y_top"]), 0.0, flight1_h + 900.0)

            xr1 = sc["x_right_min"]
            xr2 = sc["x_right_max"]

            for i in range(num_steps):
                y_s = sc["y_top"] - i * y_step_pitch
                y_e = sc["y_top"] - (i + 1) * y_step_pitch
                z_s = flight1_h + i * dz
                z_e = flight1_h + (i + 1) * dz
                mesh.add_vertical_wall((xr1, y_s), (xr2, y_s), z_s, z_e)
                mesh.add_horizontal_quad((xr1, y_s), (xr2, y_s), (xr2, y_e), (xr1, y_e), z=z_e)

            mesh.add_vertical_wall((xr1, sc["y_top"]), (xr1, sc["y_bottom"]), flight1_h, flight2_h + 900.0)
            mesh.add_vertical_wall((xl2, sc["y_top"]), (xr1, sc["y_top"]), flight1_h, flight1_h + 900.0)
            mesh.add_box(xl2 - 60.0, sc["y_bottom"] - 60.0, 0.0, xl2 + 60.0, sc["y_bottom"] + 60.0, 1000.0)

        # 3 Tam Cap Steps
        riser_h = 150.0
        for tc in tam_cap_zones:
            if tc["type"] == "stepped_x":
                steps_x = tc["x_steps"]
                y1, y2 = tc["y_min"], tc["y_max"]
                n = len(steps_x) - 1
                for i in range(n):
                    sx1 = steps_x[i]
                    sx2 = steps_x[i+1]
                    z_cur = (i + 1) * riser_h
                    z_prev = i * riser_h
                    mesh.add_vertical_wall((sx1, y1), (sx1, y2), z_prev, z_cur)
                    mesh.add_horizontal_quad((sx1, y1), (sx1, y2), (sx2, y2), (sx2, y1), z=z_cur)
                    mesh.add_vertical_wall((sx1, y1), (sx2, y1), 0.0, z_cur)
                    mesh.add_vertical_wall((sx1, y2), (sx2, y2), 0.0, z_cur)
                mesh.add_vertical_wall((steps_x[-1], y1), (steps_x[-1], y2), 0.0, n * riser_h)

            elif tc["type"] == "stepped_y":
                steps_y = tc["y_steps"]
                x1, x2 = tc["x_min"], tc["x_max"]
                n = len(steps_y) - 1
                for i in range(n):
                    sy1 = steps_y[i]
                    sy2 = steps_y[i+1]
                    z_cur = (i + 1) * riser_h
                    z_prev = i * riser_h
                    mesh.add_vertical_wall((x1, sy1), (x2, sy1), z_prev, z_cur)
                    mesh.add_horizontal_quad((x1, sy1), (x2, sy1), (x2, sy2), (x1, sy2), z=z_cur)
                    mesh.add_vertical_wall((x1, sy1), (x1, sy2), 0.0, z_cur)
                    mesh.add_vertical_wall((x2, sy1), (x2, sy2), 0.0, z_cur)

        # Slope Ramp
        for r in ramp_zones:
            add_ramp_to_mesh(mesh, r)

        return mesh

    def build_ramp_mesh(scale, offset):
        mesh = ObjMeshBuilder("Ramp", scale=scale, offset=offset)
        mesh.material = "mat_stair"
        for r in ramp_zones:
            add_ramp_to_mesh(mesh, r)
        return mesh

    configs = [
        ("meters", 0.001, (origin_x, origin_y, 0), out_m),
        ("cad_mm", 1.0, (0, 0, 0), out_mm)
    ]

    summary = {
        "status": "success",
        "meters_folder": out_m,
        "mm_folder": out_mm,
        "models": {}
    }

    for label, scale, offset, folder in configs:
        mtl_name = "materials.mtl"
        write_mtl(os.path.join(folder, mtl_name))

        w_mesh = build_wall_mesh(scale, offset)
        w_mesh.write_obj(os.path.join(folder, "wall.obj"), mtl_name)

        d_mesh = build_door_mesh(scale, offset)
        d_mesh.write_obj(os.path.join(folder, "door.obj"), mtl_name)

        win_mesh = build_window_mesh(scale, offset)
        win_mesh.write_obj(os.path.join(folder, "window.obj"), mtl_name)

        s_mesh = build_stair_mesh(scale, offset)
        s_mesh.write_obj(os.path.join(folder, "stair.obj"), mtl_name)

        r_mesh = build_ramp_mesh(scale, offset)
        r_mesh.write_obj(os.path.join(folder, "ramp.obj"), mtl_name)

        full_path = os.path.join(folder, "building_full.obj")
        with open(full_path, "w", encoding="utf-8") as f:
            f.write("# Complete Architectural 3D Model with 3 Tam Cap, Slope Ramp & Corrected Stairs\n")
            f.write(f"mtllib {mtl_name}\n\n")

            v_offset = 0
            for m in [w_mesh, d_mesh, win_mesh, s_mesh]:
                f.write(f"o {m.name}\n")
                f.write(f"usemtl {m.material}\n")
                for v in m.vertices:
                    f.write(f"v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n")
                for face in m.faces:
                    f.write(f"f {' '.join(str(idx + v_offset) for idx in face)}\n")
                v_offset += len(m.vertices)

    # Calculate statistics on meters files
    for m_name in ["wall.obj", "door.obj", "window.obj", "stair.obj", "ramp.obj", "building_full.obj"]:
        fpath = os.path.join(out_m, m_name)
        try:
            tm = trimesh.load(fpath, force="mesh")
            bmin = tm.bounds[0]
            bmax = tm.bounds[1]
            summary["models"][m_name] = {
                "vertices": int(len(tm.vertices)),
                "faces": int(len(tm.faces)),
                "width_m": round(float(bmax[0] - bmin[0]), 2),
                "depth_m": round(float(bmax[1] - bmin[1]), 2),
                "height_m": round(float(bmax[2] - bmin[2]), 2),
                "file_size_kb": round(os.path.getsize(fpath) / 1024, 1),
                "download_url": f"/api/cad/3d-models/{m_name}"
            }
        except Exception as ex:
            summary["models"][m_name] = {
                "file_size_kb": round(os.path.getsize(fpath) / 1024, 1) if os.path.exists(fpath) else 0,
                "error": str(ex),
                "download_url": f"/api/cad/3d-models/{m_name}"
            }

    # Also copy or sync to default autocad_3d_obj folder for immediate availability
    for f in Path(out_m).glob("*"):
        try:
            shutil.copy2(f, os.path.join(AUTOCAD_3D_OBJ_DIR, f.name))
        except Exception:
            pass

    return summary


def get_available_cad_assets():
    """Lấy danh sách các file model 3D, kết quả vision và trạng thái hiện tại."""
    res = {
        "clipboard_has_cad": check_clipboard_has_autocad(),
        "acad_installed": is_acad_available(),
        "models": {},
        "vision": {
            "has_result": False,
            "counts": {},
            "annotated_image": None,
            "base_image": None
        }
    }

    # Check OBJ files
    models_dir = os.path.join(AUTOCAD_3D_OBJ_DIR, "models_export", "meters")
    if not os.path.exists(models_dir) or not os.path.exists(os.path.join(models_dir, "building_full.obj")):
        models_dir = AUTOCAD_3D_OBJ_DIR

    for m_name in ["building_full.obj", "wall.obj", "door.obj", "window.obj", "stair.obj", "ramp.obj", "materials.mtl"]:
        p = os.path.join(models_dir, m_name)
        if os.path.exists(p):
            res["models"][m_name] = {
                "file_size_kb": round(os.path.getsize(p) / 1024, 1),
                "download_url": f"/api/cad/3d-models/{m_name}",
                "exists": True
            }
        else:
            res["models"][m_name] = {"exists": False}

    # Check Vision results
    v_dir = DEFAULT_VISION_DIR
    v_json = os.path.join(v_dir, "detection_result.json")
    if os.path.exists(v_json):
        try:
            with open(v_json, "r", encoding="utf-8") as f:
                v_data = json.load(f)
            res["vision"]["has_result"] = True
            res["vision"]["counts"] = v_data.get("counts", {})
            res["vision"]["cad_extents_mm"] = v_data.get("cad_extents_mm", {})
            res["vision"]["annotated_image"] = "/api/cad/vision-image/floorplan_annotated.png"
            res["vision"]["base_image"] = "/api/cad/vision-image/floorplan_base.png"
            res["vision"]["doors_sample"] = v_data.get("doors", [])[:6]
            res["vision"]["doors"] = v_data.get("doors", [])
            res["vision"]["windows"] = v_data.get("windows", [])
            res["vision"]["columns"] = v_data.get("columns", [])
            res["vision"]["walls"] = v_data.get("walls", [])
            res["vision"]["stairs"] = v_data.get("stairs", [])
            res["vision"]["tam_cap"] = v_data.get("tam_cap", [])
            res["vision"]["ramps"] = v_data.get("ramps", [])
        except Exception:
            pass

    return res
