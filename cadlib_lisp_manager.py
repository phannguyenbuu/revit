#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
cadlib_lisp_manager.py
Quét, phân tích tính năng, lệnh tắt và quản lý thư viện script & plugin AutoCAD từ:
1. D:\Dropbox\CADLib\lisp
2. D:\Dropbox\VS Projects\ACadScript
"""

import os
import sys
import re
import glob
import time
import subprocess

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import send_to_acad

SOURCES = [
    {
        "id": "cadlib",
        "name": "CADLib LISP",
        "path": r"D:\Dropbox\CADLib\lisp"
    },
    {
        "id": "acadscript",
        "name": "ACadScript",
        "path": r"D:\Dropbox\VS Projects\ACadScript"
    }
]

VALID_EXTS = {".lsp", ".scr", ".py", ".cs"}
IGNORE_DIRS = {"obj", "packages", ".vs", "bin", "properties", "_backup", "_tmp", "asset"}

_CACHED_CAD_DATA = None
_LAST_SCAN_TIME = 0

# Regex trích xuất lệnh
RE_LISP_CMD = re.compile(r'\(defun\s+(?:c:|C:)([a-zA-Z0-9_\-\+]+)')
RE_CS_CMD = re.compile(r'\[CommandMethod\s*\(\s*["\']([^"\']+)["\']', re.IGNORECASE)

EXPLICIT_CAD_NAMES = {
    "conv.lsp": "Chuyển Đổi Định Dạng Bản Vẽ CAD (Convert Script)",
    "conv_dwf.lsp": "Chuyển Đổi Bản Vẽ Sang Định Dạng DWF (Convert DWF)",
    "conv_dwf_final.lsp": "Xuất DWF Hoàn Chỉnh (Convert DWF Final)",
    "conv_dwf_simple.lsp": "Xuất DWF Tinh Gọn (Convert DWF Simple)",
    "conv_dxf_clean.lsp": "Làm Sạch & Chuyển Đổi Sang DXF (Clean DXF)",
    "conv_dxf_final.lsp": "Xuất DXF Hoàn Chỉnh (Convert DXF Final)",
    "phase1_export_acad.lsp": "Giai Đoạn 1: Xuất Bản Vẽ AutoCAD Tự Động (Phase 1)",
    "phase2_dxfout.lsp": "Giai Đoạn 2: Xuất Khối DXF Ra File (Phase 2 DXF)",
    "test_dwf.lsp": "Kiểm Tra Xuất DWF AutoCAD (Test DWF)",
    "check_dxf_circles.py": "Kiểm Tra & Đếm Đối Tượng Tròn DXF (Check Circles)",
    "clean_dxf.py": "Dọn Dẹp & Lọc Rác File Bản Vẽ DXF (Clean DXF)",
    "debug_dxf.py": "Gỡ Lỗi Cấu Trúc Dữ Liệu File DXF (Debug DXF)",
    "dxf_processor.py": "Bộ Xử Lý & Chuẩn Hóa Thực Thể DXF (DXF Processor)",
    "final_com_process.py": "Xử Lý Hoàn Thiện Bản Vẽ Qua AutoCAD COM (COM Process)",
    "full_batch_process.py": "Quy Trình Xử Lý Hàng Loạt Toàn Bộ Bản Vẽ (Batch Process)",
    "inspect_entities.py": "Kiểm Tra & Phân Tích Thực Thể Bản Vẽ (Inspect Entities)",
    "process_steelhouse.py": "Xử Lý & Dựng Bản Vẽ Nhà Khung Thép (Steelhouse)",
    "rps_dump.py": "Trích Xuất Dữ Liệu Revit / CAD Script (RPS Dump)",
    "commands.cs": "Bảng Điều Khiển Lệnh AutoCAD C# (Commands Controller)",
    "aec dimension create.cs": "Tạo Đường Dim Kích Thước AEC (AEC Dimension Create)",
    "batchconvertdxf.cs": "Chuyển Đổi Hàng Loạt Bản Vẽ DXF (Batch Convert DXF)",
    "polyline curve.cs": "Làm Cong & Mượt Tuyến Polyline (Polyline Curve)",
    "arc fillet.cs": "Bo Góc Cung Tròn Arc (Arc Fillet)",
    "area sum.cs": "Tính Tổng Diện Tích Miền (Area Sum)",
    "connect zigzag.cs": "Nối Các Đoạn Đường ZigZag (Connect ZigZag)",
    "door schedule.cs": "Bảng Thống Kê Cửa Đi & Cửa Sổ (Door Schedule)",
    "draw beam.cs": "Vẽ Dầm Kết Cấu Thép / Bê Tông (Draw Beam)",
    "hatch pattern.cs": "Quản Lý & Tạo Mẫu Hatch (Hatch Pattern)",
    "polyline align text.cs": "Căn Chỉnh Chữ Text Dọc Theo Polyline (Align Text)",
    "polyline area.cs": "Đo Diện Tích Vùng Khép Kín Polyline (Polyline Area)",
    "polyline closed.cs": "Tự Động Đóng Kín Tuyến Polyline (Polyline Closed)",
    "polyline elevator.cs": "Dựng Hình Thang Máy Bằng Polyline (Elevator Polyline)",
    "polyline fix area.cs": "Hiệu Chỉnh & Sửa Diện Tích Polyline (Fix Area)",
    "polyline line parallel.cs": "Tạo Tuyến Song Song Với Polyline (Parallel Lines)",
    "polyline road and tree.cs": "Vẽ Đường Giao Thông & Cây Cối (Road & Tree)",
    "polyline stair.cs": "Dựng Chi Tiết Cầu Thang Bằng Polyline (Stair Polyline)",
    "polyline to wall.cs": "Chuyển Đổi Polyline Sang Tường Kiến Trúc (Polyline to Wall)",
    "polyline union.cs": "Hợp Nhất Các Tuyến Polyline (Polyline Union)",
    "polyline weld.cs": "Hàn Các Đoạn Đỉnh Polyline Lại Với Nhau (Polyline Weld)",
    "planning ceiling.cs": "Mặt Bằng Bố Trí Trần Thạch Cao (Ceiling Plan)",
    "toilet tiles counter.cs": "Đếm & Bóc Tách Gạch Ốp WC (Toilet Tiles Counter)",
    "wall info.cs": "Bóc Tách Thông Tin & Thể Tích Tường (Wall Info)",
    "wall export.cs": "Xuất Dữ Liệu Tường Sang Bản Vẽ (Wall Export)",
    "table block schedule.cs": "Tạo Bảng Thống Kê Block Tự Động (Block Schedule)",
    "table door schedule.cs": "Tạo Bảng Thống Kê Cửa Đi (Door Schedule Table)",
    "beam extract from plan.cs": "Trích Xuất Dầm Từ Mặt Bằng Kết Cấu (Beam Extract)",
    "show column text.cs": "Hiển Thị Ký Hiệu & Tên Cột Kết Cấu (Column Text)"
}

CAD_WORD_MAP = {
    "dim": "Kích Thước Dim", "dimalign": "Căn Thẳng Dim", "align": "Căn Chỉnh",
    "text": "Chữ Text", "txt": "Chữ Text", "block": "Block", "clone": "Nhân Bản",
    "wall": "Tường", "door": "Cửa", "window": "Cửa Sổ", "stair": "Cầu Thang",
    "beam": "Dầm Kết Cấu", "column": "Cột Kết Cấu", "layer": "Layer",
    "export": "Xuất File", "import": "Nhập File", "batch": "Hàng Loạt",
    "polyline": "Tuyến Polyline", "pline": "Polyline", "area": "Diện Tích",
    "hatch": "Vùng Hatch", "arc": "Cung Tròn Arc", "curve": "Đường Cong",
    "fillet": "Bo Góc", "weld": "Hàn Đỉnh", "union": "Hợp Khối", "slice": "Cắt Lát",
    "plot": "In Bản Vẽ Plot", "table": "Bảng Biểu", "schedule": "Thống Kê",
    "ceiling": "Trần Thạch Cao", "tile": "Gạch Lát", "tiles": "Gạch Ốp Lát",
    "steel": "Kết Cấu Thép", "rebar": "Cốt Thép", "extract": "Trích Xuất",
    "create": "Tạo Mới", "draw": "Vẽ", "clean": "Làm Sạch", "fix": "Sửa Lỗi",
    "convert": "Chuyển Đổi", "script": "Tập Lệnh Script"
}


def determine_cad_feature_name(fname, subfolder, ext, source_name, cmds, desc):
    fname_lower = fname.lower()
    if fname_lower in EXPLICIT_CAD_NAMES:
        return EXPLICIT_CAD_NAMES[fname_lower]

    # Nếu có comment mô tả tiếng Việt tốt
    if desc and len(desc) > 5 and not desc.startswith(";") and not desc.startswith("//"):
        if any(c in desc for c in ["à", "á", "ả", "ã", "ạ", "ê", "ư", "ô", "ơ", "đ"]):
            return f"{desc.split('•')[0].strip()} ({os.path.splitext(fname)[0]})"

    base = os.path.splitext(fname)[0]
    words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\b)|[0-9]+', base)
    if not words:
        words = [base]

    translated = []
    has_vi = False
    for w in words:
        wl = w.lower()
        if wl in CAD_WORD_MAP:
            translated.append(CAD_WORD_MAP[wl])
            has_vi = True
        else:
            translated.append(w.capitalize())

    vi_phrase = " ".join(translated)
    eng_phrase = " ".join(words)

    if has_vi and vi_phrase.lower() != eng_phrase.lower():
        return f"{vi_phrase} ({eng_phrase})"
    elif eng_phrase:
        return f"Công Cụ {eng_phrase}"
    return f"Tiện Ích {base}"


def categorize_cad_script(file_name, commands, desc, ext="", subfolder=""):
    """Phân loại danh mục CAD dựa trên tên file, lệnh, phần mở rộng và mô tả."""
    s = f"{file_name} {' '.join(commands)} {desc} {subfolder}".lower()
    if any(k in s for k in ["dim", "dimalign", "aligngap", "cutdim", "gap"]):
        return "Dimension"
    elif any(k in s for k in ["text", "txt", "tahoma", "calc_txt", "font", "chữ"]):
        return "Text & Chữ"
    elif any(k in s for k in ["block", "anon2block", "a2b", "cloneblock", "cropblock", "khung", "mảng", "array"]):
        return "Block & Mảng"
    elif any(k in s for k in ["aec", "wall", "elevation", "mặt đứng", "tường", "cột", "door", "window", "stair", "beam", "dầm", "ceiling", "toilet"]):
        return "Kiến Trúc & AEC"
    elif any(k in s for k in ["polyline", "pline", "curve", "fillet", "zigzag", "weld", "hatch", "arc", "line", "stretch"]):
        return "Polyline & Hình Học"
    elif any(k in s for k in ["layer", "black", "aci", "color", "màu"]):
        return "Layer & Nét In"
    elif any(k in s for k in ["export", "import", "batch", "dxf", "dwg", "dwf", "svg", "chuyển đổi", "plot", "pdf"]):
        return "Xuất Nhập & File"
    elif any(k in s for k in ["thống kê", "ptk", "steel", "thép", "diện tích", "khối lượng", "table", "schedule", "area"]):
        return "Thống Kê & Tính Toán"
    elif ext == ".py":
        return "Python CAD"
    elif ext == ".scr":
        return "AutoCAD Script"
    elif ext == ".cs":
        return "C# .NET Plugin"
    return "Tiện Ích Khác"


def parse_cad_file(file_path, source_id, source_name, base_path):
    fname = os.path.basename(file_path)
    ext = os.path.splitext(fname)[1].lower()
    rel_path = os.path.relpath(file_path, base_path).replace("\\", "/")
    rel_dir = os.path.dirname(rel_path)
    subfolder = "" if rel_dir == "." else rel_dir

    content = ""
    for enc in ["utf-8", "cp1258", "cp1252", "latin-1"]:
        try:
            with open(file_path, "r", encoding=enc) as f:
                content = f.read()
            break
        except Exception:
            pass
    if not content:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            pass

    # Tìm lệnh
    cmds = []
    if ext == ".lsp":
        raw_cmds = RE_LISP_CMD.findall(content)
        for c in raw_cmds:
            if c not in cmds:
                cmds.append(c)
    elif ext == ".cs":
        raw_cmds = RE_CS_CMD.findall(content)
        for c in raw_cmds:
            if c not in cmds:
                cmds.append(c)

    # Đọc comment khối ;| ... |;
    block_comments = re.findall(r';\|(.*?)\|;', content, re.DOTALL)

    # Đọc comment đầu file
    lines = content.splitlines()
    desc_lines = []

    for l in lines[:40]:
        l_str = l.strip()
        if l_str.startswith(";") or l_str.startswith("//") or l_str.startswith("#"):
            c = re.sub(r'^[;\s\*\=\-\#\/]+', '', l_str).strip()
            if c and not c.startswith("---") and not c.startswith("===") and len(c) > 3:
                if not any(ign in c.lower() for ign in ["copyright", "(c)", "using ", "<auto", "<summary", "</summary"]):
                    desc_lines.append(c)
        elif l_str and not (l_str.startswith(";") or l_str.startswith("//") or l_str.startswith("#")) and len(desc_lines) >= 1:
            break

    if block_comments:
        for bc in block_comments:
            clean_bc = [line.strip() for line in bc.splitlines() if line.strip()]
            desc_lines.extend(clean_bc[:4])

    clean_desc = []
    for d in desc_lines:
        if d not in clean_desc and not d.startswith("vl-load-com") and not d.startswith("(vl-load"):
            clean_desc.append(d)

    summary = " • ".join(clean_desc[:4])
    feature_name = determine_cad_feature_name(fname, subfolder, ext, source_name, cmds, summary)

    if not summary:
        cmd_str = ", ".join(cmds) if cmds else "Nạp tự động"
        summary = f"{feature_name}. Lệnh thực thi: {cmd_str}"

    category = categorize_cad_script(fname, cmds, summary, ext, subfolder)
    fwd_path = file_path.replace("\\", "/")

    return {
        "file": fname,
        "featureName": feature_name,
        "title": feature_name,
        "ext": ext,
        "source": source_name,
        "sourceId": source_id,
        "subfolder": subfolder,
        "relPath": rel_path,
        "fullPath": fwd_path,
        "commands": cmds,
        "description": summary,
        "category": category,
        "sizeBytes": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
        "modTime": os.path.getmtime(file_path) if os.path.exists(file_path) else 0
    }


def get_cadlib_lisp_list(force_reload=False):
    """Lấy danh sách siêu dữ liệu toàn bộ script từ CADLib LISP & ACadScript (có cache)."""
    global _CACHED_CAD_DATA, _LAST_SCAN_TIME
    now = time.time()
    if not force_reload and _CACHED_CAD_DATA is not None and (now - _LAST_SCAN_TIME < 60):
        return _CACHED_CAD_DATA

    all_items = []
    source_stats = {}

    for src in SOURCES:
        src_id = src["id"]
        src_name = src["name"]
        base_dir = src["path"]

        if not os.path.exists(base_dir):
            source_stats[src_name] = 0
            continue

        src_count = 0
        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d.lower() not in IGNORE_DIRS]
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in VALID_EXTS:
                    full_p = os.path.join(root, f)
                    try:
                        item = parse_cad_file(full_p, src_id, src_name, base_dir)
                        all_items.append(item)
                        src_count += 1
                    except Exception:
                        pass
        source_stats[src_name] = src_count

    # Sắp xếp theo tên file
    all_items.sort(key=lambda x: x["file"].lower())

    total_cmds = sum(len(it["commands"]) for it in all_items)

    # Thống kê danh mục
    cat_counts = {}
    for it in all_items:
        c = it["category"]
        cat_counts[c] = cat_counts.get(c, 0) + 1

    sorted_categories = sorted(cat_counts.keys(), key=lambda k: (-cat_counts[k], k))

    result = {
        "success": True,
        "message": f"Quét thành công {len(all_items)} scripts CAD với {total_cmds} lệnh AutoCAD.",
        "directory": r"D:\Dropbox\CADLib\lisp và D:\Dropbox\VS Projects\ACadScript",
        "totalFiles": len(all_items),
        "totalCommands": total_cmds,
        "sources": source_stats,
        "categories": sorted_categories,
        "categoryCounts": cat_counts,
        "items": all_items
    }

    _CACHED_CAD_DATA = result
    _LAST_SCAN_TIME = now
    return result


def load_lisp_into_acad(file_path):
    """Nạp file LISP / Script trực tiếp vào AutoCAD qua send_to_acad."""
    if not os.path.exists(file_path):
        return False, f"File không tồn tại: {file_path}"

    file_fwd = file_path.replace("\\", "/")
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".scr":
        cmd = f'(command "SCRIPT" "{file_fwd}")\n'
    else:
        cmd = f'(load "{file_fwd}")\n'
    ok, msg = send_to_acad.send_acad_command(cmd, skip_esc=True)
    return ok, msg


def open_script_in_editor(file_path):
    """Mở file script bằng trình soạn thảo (VS Code nếu có, hoặc ứng dụng mặc định)."""
    if not os.path.exists(file_path):
        return False, f"File không tồn tại: {file_path}"
    try:
        res = subprocess.run(["code", "-r", file_path], shell=True, capture_output=True, text=True, timeout=3)
        if res.returncode == 0:
            return True, f"Đã mở file bằng VS Code: {os.path.basename(file_path)}"
    except Exception:
        pass

    try:
        os.startfile(file_path)
        return True, f"Đã mở file bằng ứng dụng mặc định: {os.path.basename(file_path)}"
    except Exception as ex:
        return False, f"Không thể mở file: {ex}"


def open_containing_folder(file_path):
    """Mở thư mục chứa file trong Windows Explorer và chọn sẵn file."""
    if not os.path.exists(file_path):
        return False, f"Đường dẫn không tồn tại: {file_path}"
    try:
        norm = os.path.normpath(file_path)
        subprocess.Popen(f'explorer /select,"{norm}"')
        return True, f"Đã mở thư mục chứa {os.path.basename(file_path)}"
    except Exception as ex:
        return False, f"Lỗi mở thư mục: {ex}"


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    t0 = time.time()
    res = get_cadlib_lisp_list(force_reload=True)
    t1 = time.time()
    print(f"Quet hoan tat trong {t1 - t0:.2f}s:")
    print("Success:", res["success"])
    print("Total Files:", res["totalFiles"])
    print("Total Commands:", res["totalCommands"])
    print("Sources:", res["sources"])
    print("Categories:", res["categoryCounts"])
    if res["items"]:
        print("Sample item 0:", res["items"][0]["file"], "->", res["items"][0]["featureName"])
