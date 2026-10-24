"""
AutoCAD Clipboard to DXF & Vision Detection Pipeline
Author: Antigravity Assistant
Description:
1. Đọc dữ liệu AutoCAD từ Windows Clipboard (Compound OLE Stream / DWG AC1032).
2. Tự động chuyển đổi thành file DXF chuẩn (dùng AutoCAD accoreconsole hoặc ezdxf).
3. Render bản vẽ 2D với độ phân giải cao.
4. Áp dụng Computer Vision & Phân tích hình học CAD để phát hiện:
   - Cửa đi (Doors): Bounding Box, kích thước, tọa độ tâm, loại cửa (1 cánh / 2 cánh).
   - Tường (Walls): Bounding Box, hướng (Ngang / Dọc), chiều dài, tọa độ.
   - Cột kết cấu (Columns): Vị trí và kích thước cột.
   - Cửa sổ (Windows): Bounding Box và vị trí.
5. Xuất ảnh đã vẽ Bbox & Nhãn, các ảnh crop chi tiết, và file dữ liệu JSON.
"""

import sys
import os

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import struct
import subprocess
import json
import numpy as np
import cv2
import ezdxf
from ezdxf.bbox import extents
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import matplotlib.pyplot as plt

def get_clipboard_ole_stream(out_bin_path):
    """Trích xuất stream AutoCAD OLE từ Clipboard Windows qua PowerShell."""
    ps_cmd = f"""
    Add-Type -AssemblyName System.Windows.Forms
    $data = [System.Windows.Forms.Clipboard]::GetDataObject()
    if ($null -eq $data) {{ exit 1 }}
    if ($data.GetDataPresent('Embed Source')) {{
        $ms = $data.GetData('Embed Source')
        if ($ms -is [System.IO.MemoryStream]) {{
            [System.IO.File]::WriteAllBytes('{out_bin_path}', $ms.ToArray())
            exit 0
        }}
    }}
    exit 2
    """
    res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
    if res.returncode != 0 or not os.path.exists(out_bin_path):
        raise RuntimeError("Không tìm thấy dữ liệu AutoCAD OLE ('Embed Source') trong Clipboard!")
    print(f"[1/5] Đã trích xuất OLE Clipboard ({os.path.getsize(out_bin_path)} bytes)")

def extract_dwg_from_ole(ole_path, out_dwg_path):
    """Trích xuất file DWG nguyên bản từ OLE Compound Document."""
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
                print(f"[2/5] Đã trích xuất DWG ({s_data[:6].decode('latin1')}, {size} bytes) -> {out_dwg_path}")
                dwg_found = True
                break
                
    if not dwg_found:
        raise RuntimeError("Không tìm thấy stream DWG (AC10xx) trong dữ liệu OLE!")

def convert_dwg_to_dxf(dwg_path, out_dxf_path, acad_dir=r"C:\Program Files\Autodesk\AutoCAD 2022"):
    """Dùng accoreconsole để chuyển DWG sang DXF nhanh chóng và chuẩn xác tuyệt đối."""
    accore = os.path.join(acad_dir, "accoreconsole.exe")
    if not os.path.exists(accore):
        raise FileNotFoundError(f"Không tìm thấy accoreconsole.exe tại {accore}")
    
    scr_path = os.path.join(os.path.dirname(out_dxf_path), "_temp_export.scr")
    formatted_dxf = out_dxf_path.replace("\\", "/")
    with open(scr_path, "w", encoding="utf-8") as f:
        f.write(f'DXFOUT "{formatted_dxf}" 16\nQUIT\n')
        
    cmd = [accore, "/i", dwg_path, "/s", scr_path]
    subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(scr_path):
        os.remove(scr_path)
        
    if not os.path.exists(out_dxf_path):
        raise RuntimeError("Chuyển đổi DWG sang DXF thất bại!")
    print(f"[3/5] Đã lưu DXF thành công -> {out_dxf_path} ({os.path.getsize(out_dxf_path):,} bytes)")

def run_vision_detection(dxf_path, output_dir):
    """Phân tích thực thể, render và nhận diện tường, cửa, bbox, vị trí."""
    os.makedirs(output_dir, exist_ok=True)
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    
    bb = extents(msp)
    margin = 500.0
    min_x, max_x = bb.extmin.x - margin, bb.extmax.x + margin
    min_y, max_y = bb.extmin.y - margin, bb.extmax.y + margin
    cad_w, cad_h = max_x - min_x, max_y - min_y
    
    img_w = 4000
    img_h = int(img_w * (cad_h / cad_w))
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
    print(f"[4/5] Đã render mặt bằng 2D -> {clean_base}")
    
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
        except:
            continue
            
        c = ((ebb.extmin.x + ebb.extmax.x)/2, (ebb.extmin.y + ebb.extmax.y)/2)
        
        if any(k in layer for k in ["A-DOOR", "32-CUA", "CUA", "DOOR"]) and not any(k in layer for k in ["CUA SO", "CUA-SO"]):
            doors_raw.append({"entity": etype, "min": (ebb.extmin.x, ebb.extmin.y), "max": (ebb.extmax.x, ebb.extmax.y), "center": c})
        elif any(k in layer for k in ["CUA SO", "CUA-SO", "WINDOW", "GLAZ"]):
            windows_raw.append({"entity": etype, "min": (ebb.extmin.x, ebb.extmin.y), "max": (ebb.extmax.x, ebb.extmax.y), "center": c})
        elif any(k in layer for k in ["COT", "COLU"]):
            columns_raw.append({"entity": etype, "min": (ebb.extmin.x, ebb.extmin.y), "max": (ebb.extmax.x, ebb.extmax.y), "center": c})
        elif any(k in layer for k in ["TUONG", "A-WALL", "WALL", "S5", "NET03", "NET-02", "N THAY 0.25"]):
            dx = ebb.extmax.x - ebb.extmin.x
            dy = ebb.extmax.y - ebb.extmin.y
            length = max(dx, dy)
            if length > 250:
                walls_raw.append({"entity": etype, "min": (ebb.extmin.x, ebb.extmin.y), "max": (ebb.extmax.x, ebb.extmax.y), "center": c, "length": length, "orientation": "Horizontal" if dx > dy else "Vertical"})

    # Cluster doors
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
    windows = cluster_items(windows_raw, max_d=1800, min_sz=500, max_sz=4000)
    columns = cluster_items(columns_raw, max_d=600, min_sz=100, max_sz=1500)
    major_walls = [w for w in walls_raw if w["length"] >= 800]

    vis_img = cv2.imread(clean_base)
    crops_dir = os.path.join(output_dir, "crops")
    os.makedirs(crops_dir, exist_ok=True)

    results = {
        "cad_file": dxf_path,
        "cad_extents_mm": {"width": round(cad_w, 1), "height": round(cad_h, 1)},
        "counts": {"doors": len(doors), "windows": len(windows), "columns": len(columns), "major_walls": len(major_walls)},
        "doors": [], "walls": [], "columns": [], "windows": []
    }

    # Annotate Walls (Red)
    for i, w in enumerate(major_walls):
        px1, py1, px2, py2 = cad_bbox_to_pixel(*w["min"], *w["max"])
        cv2.rectangle(vis_img, (px1, py1), (max(px2, px1+2), max(py2, py1+2)), (0, 0, 255), 2)
        results["walls"].append({"id": f"WALL_{i+1:03d}", "orientation": w["orientation"], "length_mm": round(w["length"], 1), "center_cad": [round(w["center"][0], 1), round(w["center"][1], 1)], "bbox_pixels": [px1, py1, px2, py2]})

    # Annotate Columns (Yellow)
    for i, col in enumerate(columns):
        px1, py1, px2, py2 = cad_bbox_to_pixel(*col["min"], *col["max"])
        cv2.rectangle(vis_img, (px1, py1), (px2, py2), (0, 215, 255), 2)
        results["columns"].append({"id": f"COL_{i+1:02d}", "dimension_mm": f"{col['width_mm']}x{col['depth_mm']}", "center_cad": [round(col["center"][0], 1), round(col["center"][1], 1)], "bbox_pixels": [px1, py1, px2, py2]})

    # Annotate Windows (Cyan)
    for i, win in enumerate(windows):
        px1, py1, px2, py2 = cad_bbox_to_pixel(*win["min"], *win["max"])
        cv2.rectangle(vis_img, (px1, py1), (px2, py2), (255, 255, 0), 2)
        results["windows"].append({"id": f"WIN_{i+1:02d}", "width_mm": win["width_mm"], "center_cad": [round(win["center"][0], 1), round(win["center"][1], 1)], "bbox_pixels": [px1, py1, px2, py2]})

    # Annotate Doors (Green) & Save Crops
    for i, d in enumerate(doors):
        d_id = f"DOOR_{i+1:02d}"
        px1, py1, px2, py2 = cad_bbox_to_pixel(*d["min"], *d["max"])
        px1, py1 = max(0, px1 - 6), max(0, py1 - 6)
        px2, py2 = min(img_w - 1, px2 + 6), min(img_h - 1, py2 + 6)
        cv2.rectangle(vis_img, (px1, py1), (px2, py2), (0, 255, 0), 3)
        
        lbl = f"{d_id} ({int(d['width_mm'])}mm)"
        (tw, th), _ = cv2.getTextSize(lbl, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(vis_img, (px1, max(0, py1 - th - 8)), (min(img_w - 1, px1 + tw + 10), py1), (0, 180, 0), -1)
        cv2.putText(vis_img, lbl, (px1 + 5, py1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2, cv2.LINE_AA)
        
        crop = vis_img[max(0, py1-40):min(img_h-1, py2+40), max(0, px1-40):min(img_w-1, px2+40)]
        crop_file = os.path.join(crops_dir, f"{d_id}.png")
        cv2.imwrite(crop_file, crop)
        
        results["doors"].append({
            "id": d_id,
            "type": "Cửa đi 2 cánh" if d["width_mm"] >= 1300 else "Cửa đi 1 cánh",
            "width_mm": d["width_mm"],
            "center_cad": [round(d["center"][0], 1), round(d["center"][1], 1)],
            "bbox_pixels": [px1, py1, px2, py2],
            "crop_path": crop_file
        })

    annotated_path = os.path.join(output_dir, "floorplan_annotated.png")
    cv2.imwrite(annotated_path, vis_img)
    json_path = os.path.join(output_dir, "detection_result.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    print(f"[5/5] Hoàn tất nhận diện! Ảnh đã vẽ bbox: {annotated_path}")
    print(f"      Dữ liệu JSON: {json_path}")
    return results

if __name__ == "__main__":
    work_dir = r"C:\Users\Admin\.gemini\antigravity\scratch"
    ole_f = os.path.join(work_dir, "clipboard_raw.bin")
    dwg_f = os.path.join(work_dir, "clipboard_model.dwg")
    dxf_f = os.path.join(work_dir, "clipboard_model.dxf")
    
    get_clipboard_ole_stream(ole_f)
    extract_dwg_from_ole(ole_f, dwg_f)
    convert_dwg_to_dxf(dwg_f, dxf_f)
    run_vision_detection(dxf_f, os.path.join(work_dir, "vision_output"))
