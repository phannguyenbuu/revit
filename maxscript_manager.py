#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
maxscript_manager.py
Quản lý, phân tích metadata, tìm kiếm và tổng hợp kho Maxscript & Python 3ds Max từ:
1. D:\Dropbox\skMSTool
2. C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Documents\3ds Max 2022\scripts
"""

import os
import sys
import re
import glob
import time
import subprocess

SOURCES = [
    {
        "id": "skmstool",
        "name": "skMSTool",
        "path": r"D:\Dropbox\skMSTool"
    },
    {
        "id": "user3dsmax2022",
        "name": "3ds Max 2022",
        "path": r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Documents\3ds Max 2022\scripts"
    }
]

VALID_EXTS = {".ms", ".mcr", ".mse", ".py"}

_CACHED_MAXSCRIPT_DATA = None
_LAST_SCAN_TIME = 0

# Regex patterns for MaxScript parsing
RE_MACRO = re.compile(r'macroscript\s+([a-zA-Z0-9_]+)', re.IGNORECASE)
RE_CAT = re.compile(r'category\s*:\s*["\']([^"\']+)["\']', re.IGNORECASE)
RE_TOOLTIP = re.compile(r'tooltip\s*:\s*["\']([^"\']+)["\']', re.IGNORECASE)
RE_BTN = re.compile(r'buttontext\s*:\s*["\']([^"\']+)["\']', re.IGNORECASE)
RE_ROLLOUT = re.compile(r'rollout\s+([a-zA-Z0-9_]+)\s+["\']([^"\']+)["\']', re.IGNORECASE)
RE_UTILITY = re.compile(r'utility\s+([a-zA-Z0-9_]+)\s+["\']([^"\']+)["\']', re.IGNORECASE)


def parse_skmenulist():
    r"""Đọc file D:\Dropbox\skMSTool\skmenulist.txt để tra cứu tên hiển thị & nhóm menu."""
    menu_path = r"D:\Dropbox\skMSTool\skmenulist.txt"
    menu_map = {}
    if not os.path.exists(menu_path):
        return menu_map

    try:
        current_cat = "Chung"
        with open(menu_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("-"):
                    continue
                if "(" in line and "|" not in line:
                    current_cat = line.split("(")[0].strip()
                    continue
                elif line == ")":
                    current_cat = "Chung"
                    continue

                parts = line.split("|")
                if len(parts) == 3:
                    code, title, filename = parts[0].strip(), parts[1].strip(), parts[2].strip()
                    menu_map[filename.lower()] = {
                        "code": code,
                        "title": title,
                        "category": current_cat
                    }
    except Exception:
        pass
    return menu_map


# Từ điển tên tính năng tiếng Việt chi tiết cho các script cốt lõi
EXPLICIT_FEATURE_NAMES = {
    # 3ds Max 2022 User Scripts
    "detachelements.ms": "Tách Từng Element Poly Thành Object Riêng (Detach Elements)",
    "detachelementstonodes.ms": "Tách Element Thành Các Node Độc Lập (Detach to Nodes)",
    "exportcroppeddiffusetexture.ms": "Cắt & Xuất Texture Diffuse Tự Động (Crop Texture)",
    "exportmeshtovectorpdf.ms": "Xuất Lưới 3D Sang Bản Vẽ Vector PDF (Mesh to PDF)",
    "exportselectedtoobj.ms": "Xuất Vật Thể Đang Chọn Sang File OBJ (Export OBJ)",
    "exportsplinetojson.ms": "Xuất Tọa Độ Spline Sang JSON (Spline to JSON)",
    "export_by_rect.ms": "Xuất Mô Hình Theo Khung Chữ Nhật Quét Chọn (Export by Rect)",
    "export_ifc_iso_occt_freecad.py": "Chuyển Đổi Mô Hình IFC Qua FreeCAD OCCT (IFC ISO Export)",
    "export_lights.ms": "Xuất Danh Sách & Thông Số Đèn Chiếu Sáng (Export Lights)",
    "export_selection_pos_json.ms": "Xuất Tọa Độ Vị Trí Đối Tượng Sang JSON (Export Position)",
    "export_selection_projections.ms": "Xuất Hình Chiếu Các Mặt Của Vật Thể (Export Projections)",
    "export_vray_datasmith.ms": "Xuất Scene V-Ray Sang Unreal Datasmith (Export Datasmith)",
    "filter_plates_different_from_6mm.ms": "Lọc Các Bản Mã Thép Khác Dày 6mm (Filter 6mm)",
    "filter_standing_plates_different_from_10mm.ms": "Lọc Bản Mã Thép Đứng Khác Dày 10mm (Filter 10mm)",
    "fix_bolt_size_selection.ms": "Chuẩn Hóa Kích Thước Bu-lông Đang Chọn (Fix Bolt Size)",
    "fix_viewport_shading.ms": "Sửa Lỗi Hiển Thị Đổ Bóng Viewport 3ds Max (Fix Shading)",
    "fix_viewport_shading_deep.ms": "Sửa Triệt Để Lỗi Vật Liệu/Shading Viewport (Fix Viewport Deep)",
    "flattenfaces3points.ms": "Làm Phẳng Mặt Poly Qua 3 Điểm Chuẩn (Flatten Faces 3P)",
    "get_view_properties.ms": "Lấy Thông Số Góc Nhìn Viewport & Camera (View Properties)",
    "ifc_to_dxf_clean_braces.py": "Chuyển IFC Sang DXF & Làm Sạch Giằng Thép (IFC to DXF)",
    "ifc_to_dxf_rule_export.py": "Xuất Bản Vẽ DXF Từ IFC Theo Quy Tắc (Rule Export)",
    "importalignobj.ms": "Nhập File OBJ & Tự Động Căn Trục Tọa Độ (Import Align OBJ)",
    "import_dwg_from_clipboard.ms": "Dán & Nhập Bản Vẽ DWG Từ Clipboard Vào 3ds Max (Import DWG)",
    "instant_remesh.ms": "Làm Sạch & Phân Bổ Lại Lưới Lập Tức (Instant Remesh)",
    "make_clipboard_from_texture.ms": "Tạo Ảnh Clipboard Từ Texture Đang Chọn (Texture to CB)",
    "match_wirecolor.ms": "Đồng Bộ Màu Dây Wirecolor Theo Nhóm (Match Wirecolor)",
    "obj_to_ifc_localhost_uploader.ms": "Tải Lên File OBJ Chuyển Sang IFC Tự Động (OBJ to IFC)",
    "patch_combine_folder.py": "Gộp & Đồng Bộ Dữ Liệu Thư Mục Patch (Combine Folder)",
    "profile_drawing.py": "Vẽ Trắc Diện & Profile Đối Tượng Kết Cấu (Profile Drawing)",
    "projectvertstoshape.ms": "Chiếu Điểm Vertex Lên Đường Cong Shape (Project Verts)",
    "quicksplinesweeplength.ms": "Đo Nhanh Chiều Dài Spline Dùng Sweep (Sweep Length)",
    "rebar_analyze.ms": "Phân Tích & Bóc Tách Thép Xây Dựng (Rebar Analyze)",
    "rebar_splice.ms": "Tạo & Kiểm Tra Mối Nối Cốt Thép (Rebar Splice)",
    "reconstruct_beam_elements.ms": "Dựng Lại Hình Dầm Kết Cấu Từ Phần Tử Poly (Reconstruct Beams)",
    "remeshcleangrid.ms": "Làm Mượt Lưới & Tạo Grid Đều Đẹp (Clean Grid Remesh)",
    "renameselectionbyjointbbox.ms": "Đổi Tên Vật Thể Theo Bounding Box Khớp Nối (Joint Rename)",
    "replace_selection_with_named_clone.ms": "Thay Thế Đối Tượng Bằng Bản Sao Định Danh (Replace Clone)",
    "replace_with_bbox.ms": "Thay Thế Mô Hình Bằng Hộp Bounding Box (Replace BBox)",
    "resetxformandfixnormals.ms": "Reset XForm & Chuẩn Hóa Pháp Tuyến Normal (Reset XForm)",
    "selectbyboundingbox.ms": "Chọn Đối Tượng Nằm Trong Vùng Bounding Box (Select BBox)",
    "selectionrotator.ms": "Xoay Nhanh Nhóm Đối Tượng Theo Trục Chỉ Định (Rotate Selection)",
    "select_black_wirecolor.ms": "Chọn Tất Cả Đối Tượng Có Wirecolor Màu Đen (Select Black)",
    "select_by_bbox.ms": "Lọc Đối Tượng Theo Kích Thước Bounding Box (Select by BBox)",
    "select_large_polys.ms": "Tìm & Chọn Các Mặt Poly Có Diện Tích Lớn (Select Large Polys)",
    "select_over_1000_faces.ms": "Lọc Các Mesh Nặng Hơn 1000 Mặt (Heavy Mesh Filter)",
    "select_related_plates.ms": "Chọn Bản Mã Thép Liên Quan Đến Khớp Nối (Related Plates)",
    "set_vray_camera_far_clipping.ms": "Đặt Khoảng Cắt Xa (Far Clipping) Camera V-Ray (Far Clip)",
    "show_selection_grid_axis.ms": "Hiển Thị Trục & Lưới Tọa Độ Vật Thể (Show Grid Axis)",
    "skbrigde.ms": "Cầu Nối Đồng Bộ 3ds Max Với Revit & AEC Hub (3ds Max Bridge)",
    "smoothpolyselection.ms": "Làm Mịn Bề Mặt Vùng Chọn Editable Poly (Smooth Poly)",
    "splinesweeplengthtracker_ui.ms": "Giao Diện Đo & Theo Dõi Chiều Dài Spline (Spline Tracker)",
    "splinezonemeshgenerator.ms": "Tạo Lưới 3D Tự Động Từ Vùng Biên Spline (Zone Mesh)",
    "validate_joints_legends.ms": "Kiểm Tra Tính Hợp Lệ Của Nút Liên Kết (Validate Joints)",
    "vrayglass_assign.ms": "Gán Nhanh Vật Liệu Kính V-Ray Tiêu Chuẩn (Assign VRay Glass)",
    "codexagentbridge_3dsmax2022.ms": "Cầu Nối Điều Khiển Codex AI Cho 3ds Max (Codex Bridge)",
    "codexagentchat_3dsmax2022.ms": "Cửa Sổ Chat AI Trực Tiếp Trong 3ds Max (Codex Chat)",
    "load_bridge_in_3dsmax.ms": "Khởi Động Nhanh Codex Bridge Trong 3ds Max (Load Bridge)",
    "load_chat_in_3dsmax.ms": "Mở Giao Diện Chat AI Trong 3ds Max (Load Chat)",

    # Root skMSTool Scripts
    "1.ms": "Tạo Shortcut 3ds Max Khởi Động (Startup Shortcut)",
    "3.ms": "Tối Giản Lưới Mặt Poly (Simplify Mesh Face)",
    "x1.ms": "Copy Đối Tượng Poly Sang Clipboard (Poly to CB)",
    "glassframev03.ms": "Tạo Khung Nhôm Kính Kiến Trúc v03 (Glass Frame)",
    "batch_to_glb.ms": "Xuất Hàng Loạt Mô Hình Sang GLB / glTF",
    "ak-vrmtl to standard.ms": "Chuyển Đổi Vật Liệu V-Ray Sang Standard (VRay to Standard)",
    "skrendercamerastate.ms": "Lưu & Bật/Tắt Trạng Thái Camera / Đèn Render (Camera/Light State)",
    "skresizenode.ms": "Co Giãn Kích Thước Đối Tượng Nhanh (Resize Node)",
    "tiledata.ms": "Tính Toán & Bố Trí Dữ Liệu Gạch Lát (Tile Data)",
    "to_svg.ms": "Xuất Spline Khép Kín Sang SVG Vector (Spline to SVG)",
    "grass_generator_v1.5.mcr": "Tạo Cỏ 3D Tự Động & Bụi Cây (Grass Generator)",
    "macro_lightlist.mcr": "Quản Lý Danh Sách Nguồn Sáng Toàn Scene (Light Lister)",
    "renameduplicatedir.ms": "Đổi Tên Thư Mục Trùng Lặp Tự Động (Rename Duplicate Dir)",
    "resetvraymax.ms": "Khôi Phục Thiết Lập Render Mặc Định V-Ray (Reset V-Ray)",
    "skproxy_tmp.ms": "Tạo & Quản Lý V-Ray Proxy Tạm Thời (V-Ray Proxy Tool)",
    "sktools-menu.ms": "Cài Đặt & Nạp Menu skMSTool Lên 3ds Max (Install Menu)",
    "sktools-publish.ms": "Đóng Gói & Xuất Bản Bộ Công Cụ skMSTool (Publish Tools)",
    "excel.ms": "Đọc & Tương Tác Dữ Liệu Với Bảng Tính Excel (Excel Connect)",

    # skmenulist.txt tools
    "sk-librarymanager.mcr": "Quản Lý Thư Viện 3D (Library Manager)",
    "sk-importfromcb.ms": "Nhập Mô Hình Từ Clipboard (sk Importer)",
    "sk-roomprofile.ms": "Tạo Phào Chỉ & Profile Phòng (Room Profile)",
    "sk-keblermanager.ms": "Quản Lý Đối Tượng Phức Hợp (Kebler Manager)",
    "sk-move.mcr": "Bộ Điều Khiển Di Chuyển Chính Xác (Move Controller)",
    "sk-cbimporter.ms": "Nhập Dữ Liệu Clipboard (CB Importer)",
    "sk-syncmtl.ms": "Đồng Bộ Thuộc Tính Vật Liệu (Sync Material)",
    "sk-modcontrol.ms": "Bảng Điều Khiển Modifier Nhanh (Modifier Control)",
    "sk-alignspline.ms": "Căn Chỉnh Đường Spline / Shape (Shape Alignment)",
    "sk-copy.mcr": "Sao Chép Vật Thể Nhanh (Copy Objects)",
    "sk-paste.mcr": "Dán Vật Thể Đã Copy (Paste Objects)",
    "sk-previewimage.ms": "Lưu & Xuất Ảnh Xem Trước (Save Preview)",
    "sk-findimg.ms": "Tìm Kiếm Ảnh Texture Thiếu (Find Missing Image)",
    "sk-aecglassframe.ms": "Tạo Khung Nhôm Kính Kiến Trúc (AEC Glass Frame)",
    "sk-bricktile.ms": "Tạo Gạch Ốp Lát Kiến Trúc (Brick & Tile)",
    "sk-rename.mcr": "Đổi Tên Vật Thể Hàng Loạt (Batch Rename)",
    "sk-similar.mcr": "Chọn Các Đối Tượng Tương Tự (Select Similar)",
    "sk-scale.ms": "Co Giãn Kích Thước Linh Hoạt (Flexible Scale)",
    "sk-randomuvw.ms": "Tạo Ngẫu Nhiên Tọa Độ Map UVW (Random UVW)",
    "sk-mtllistview.ms": "Bảng Quản Lý Danh Sách Vật Liệu (Material Manager)",
    "sk-picturemtl.ms": "Gán Tranh Treo Tường Tự Động (Picture Material)",
    "sk-materialbykeyword.ms": "Lọc & Gán Vật Liệu Theo Từ Khóa (Material by Keyword)",
    "sk-batchrender.ms": "Render Hàng Loạt Tự Động (Batch Render)",
    "sk-studiorender.ms": "Render Môi Trường Studio (Studio Render)",
    "sk-topview.ms": "Render Nhanh Góc Chiếu Bằng (Top View Render)",
    "sk-renderregion.ms": "Render Vùng Chọn Chỉ Định (Region Render)",
    "sk-fixmax.ms": "Sửa Lỗi Phiên Bản V-Ray Trong File (Fix V-Ray Version)",
    "sk-repairchinese.ms": "Sửa Lỗi Ký Tự Tiếng Trung (Repair Chinese File)",
    "sk-roundnumber.ms": "Làm Tròn Số Đo & Tọa Độ (Round Numbers)",
    "sk-terrain.ms": "Dựng Địa Hình & Cao Độ Tự Động (Terrain Generator)",
    "sk-samplefile.ms": "Tạo & Nạp File Mẫu Chuẩn (Sample File)",
    "sk-quickslice.ms": "Cắt Nhanh Tiết Diện Đối Tượng (Quick Slice)",
    "sk-furniturelist.ms": "Bóc Tách Danh Mục Nội Thất (Furniture List)",
    "sk-snapshot2d.ms": "Chụp Ảnh Snapshot 2D Hình Chiếu (2D Snapshot)",
    "sk-checkuserpath.ms": "Kiểm Tra & Cập Nhật User Path (User Paths)",
    "sk-repaircorruptmax.ms": "Phục Hồi File Max Bị Lỗi (Repair Corrupt Max)",
    "sk-box2p.ms": "Tạo Khối Box Qua 2 Điểm Chọn (Box from 2 Points)",
    "vraycamlister.ms": "Quản Lý Danh Sách Camera V-Ray (V-Ray Cam Lister)",
    "sk-setcolor.ms": "Đặt Màu Sắc Wirecolor Nhanh (Set Object Color)"
}

WORD_DICTIONARY = {
    "build": "Dựng", "create": "Tạo", "make": "Tạo", "gen": "Tạo", "generator": "Tạo",
    "import": "Nhập File", "export": "Xuất File", "align": "Căn Chỉnh", "attach": "Gộp Khối",
    "detach": "Tách Khối", "select": "Chọn", "selected": "Đang Chọn", "filter": "Lọc Tuyển",
    "slice": "Cắt Tiết Diện", "draw": "Vẽ Phác Thảo", "rename": "Đổi Tên", "replace": "Thay Thế",
    "reset": "Khôi Phục", "clean": "Làm Sạch", "fix": "Sửa Lỗi", "repair": "Phục Hồi",
    "smooth": "Làm Mịn", "flatten": "Làm Phẳng", "random": "Ngẫu Nhiên", "sync": "Đồng Bộ",
    "copy": "Sao Chép", "paste": "Dán", "batch": "Hàng Loạt", "scale": "Co Giãn",
    "rotate": "Xoay", "material": "Vật Liệu", "mtl": "Vật Liệu", "texture": "Texture",
    "camera": "Camera", "cam": "Camera", "light": "Đèn", "lights": "Hệ Thống Đèn",
    "render": "Render", "mesh": "Khối Poly", "poly": "Khối Poly", "polygon": "Khối Poly",
    "spline": "Đường Spline", "spilne": "Đường Spline", "curve": "Đường Cong",
    "shape": "Hình Shape", "line": "Đường Line", "rebar": "Cốt Thép", "beam": "Dầm Kết Cấu",
    "column": "Cột Kết Cấu", "plate": "Bản Mã Thép", "bolt": "Bu-lông Liên Kết",
    "wall": "Tường", "door": "Cửa Đi", "window": "Cửa Sổ", "glass": "Kính",
    "tile": "Gạch Lát", "terrain": "Địa Hình", "grass": "Cỏ 3D", "stair": "Cầu Thang",
    "cabinet": "Tủ Nội Thất", "dwg": "Bản Vẽ DWG", "ifc": "Mô Hình IFC", "obj": "File OBJ",
    "svg": "File Vector SVG", "pdf": "File PDF", "clipboard": "Clipboard", "cb": "Clipboard",
    "library": "Thư Viện", "proxy": "V-Ray Proxy", "wirecolor": "Màu Wirecolor",
    "viewport": "Viewport", "view": "Góc Nhìn", "block": "Block", "count": "Đếm & Thống Kê",
    "manage": "Quản Lý", "manager": "Quản Lý", "tools": "Bộ Công Cụ", "tool": "Công Cụ",
    "lister": "Danh Sách", "state": "Trạng Thái", "pivot": "Tâm Trục Pivot",
    "shading": "Đổ Bóng", "joint": "Mối Nối Khớp", "face": "Mặt Poly", "vert": "Điểm Đỉnh",
    "vertex": "Điểm Đỉnh", "edge": "Cạnh Lưới", "normal": "Pháp Tuyến Normal",
    "uvw": "Tọa Độ UVW", "box": "Khối Hộp Box", "room": "Không Gian Phòng"
}


def determine_feature_name(fname, subfolder, ext, source_name, menu_info=None, tooltip="", rollout_title="", description="", macro_name=""):
    fname_lower = fname.lower()
    if fname_lower in EXPLICIT_FEATURE_NAMES:
        return EXPLICIT_FEATURE_NAMES[fname_lower]

    if menu_info and menu_info.get("title"):
        title = menu_info["title"]
        if not title.lower().startswith("sk"):
            return f"{title} ({os.path.splitext(fname)[0]})"

    # Nếu có tooltip hoặc rollout title tiếng Việt hoặc tên chức năng rõ ràng
    if tooltip and len(tooltip) > 3 and not tooltip.lower().startswith("sk") and not tooltip.endswith(".ms"):
        return f"{tooltip} ({os.path.splitext(fname)[0]})"

    if rollout_title and len(rollout_title) > 3 and not rollout_title.lower().startswith("sk"):
        return f"{rollout_title} ({os.path.splitext(fname)[0]})"

    # Phân tích cú pháp theo tên file
    base = os.path.splitext(fname)[0]
    clean_base = base
    for prefix in ["SK-", "sk_", "sk", "Macro_", "mcr_", "fn_", "lib_"]:
        if clean_base.startswith(prefix) and len(clean_base) > len(prefix) + 2:
            clean_base = clean_base[len(prefix):]
            break

    words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\b)|[0-9]+', clean_base)
    if not words:
        words = [clean_base]

    translated_words = []
    has_vi = False
    for w in words:
        wl = w.lower()
        if wl in WORD_DICTIONARY:
            translated_words.append(WORD_DICTIONARY[wl])
            has_vi = True
        else:
            translated_words.append(w.capitalize())

    vi_phrase = " ".join(translated_words)
    eng_phrase = " ".join(words)

    if has_vi and vi_phrase.lower() != eng_phrase.lower():
        return f"{vi_phrase} ({eng_phrase})"
    elif eng_phrase:
        return f"Công Cụ {eng_phrase}"
    return f"Tiện Ích {base}"


def categorize_maxscript(fname, subfolder, ext, source_name, script_cat="", menu_info=None):
    """Phân loại chủ đề cho script dựa vào metadata, menu map, folder và từ khóa."""
    if menu_info and menu_info.get("category"):
        cat = menu_info["category"]
        if cat in ["Library", "Transfer Object"]:
            return "Thư Viện & Asset"
        elif cat == "AEC Object":
            return "AEC & Kết Cấu"
        elif cat == "Material":
            return "Vật Liệu & UVW"
        elif cat == "Render":
            return "Render & Camera"
        elif cat in ["Transform", "Node", "Random"]:
            return "Modeling & Mesh"

    s = f"{fname} {subfolder}".lower()

    if ext == ".py":
        return "Python"
    if "bridge" in s or "codex" in s:
        return "Bridge & Codex"
    if ext == ".mcr" or "macro" in subfolder.lower():
        return "MacroScript & UI"
    if any(k in s for k in ["rebar", "bolt", "beam", "plate", "ifc", "aec", "wall", "door", "brick", "tile", "freecad", "joint", "steel"]):
        return "AEC & Kết Cấu"
    if any(k in s for k in ["mtl", "material", "vraymtl", "texture", "uvw", "diffuse", "glass", "color"]):
        return "Vật Liệu & UVW"
    if any(k in s for k in ["render", "camera", "light", "exposure", "corona", "vray", "batchrender", "topview"]):
        return "Render & Camera"
    if any(k in s for k in ["export", "import", "svg", "obj", "dwg", "pdf", "glb", "json", "dxf", "clipboard"]):
        return "Xuất Nhập & File"
    if any(k in s for k in ["spline", "shape", "curve", "sweep", "path", "contour"]):
        return "Spline & Đường Dẫn"
    if any(k in s for k in ["mesh", "poly", "detach", "remesh", "modify", "scale", "align", "rotat", "vertex", "face", "edge", "select", "bbox"]):
        return "Modeling & Mesh"
    if any(k in s for k in ["startup", "core", "lib", "library", "config", "def", "menu"]):
        return "Thư Viện & Startup"

    if script_cat:
        sc_lower = script_cat.lower()
        if any(k in sc_lower for k in ["render", "camera", "light", "exposure", "vray", "corona"]):
            return "Render & Camera"
        if any(k in sc_lower for k in ["mtl", "material", "texture", "uvw", "color"]):
            return "Vật Liệu & UVW"
        if any(k in sc_lower for k in ["model", "mesh", "poly", "object", "primitive", "transform"]):
            return "Modeling & Mesh"
        if any(k in sc_lower for k in ["spline", "shape", "curve"]):
            return "Spline & Đường Dẫn"
        if any(k in sc_lower for k in ["export", "import", "file"]):
            return "Xuất Nhập & File"
        if any(k in sc_lower for k in ["aec", "arch", "structure", "rebar", "wall", "dim"]):
            return "AEC & Kết Cấu"
        if any(k in sc_lower for k in ["startup", "lib", "system", "ide"]):
            return "Thư Viện & Startup"
        return "Tiện Ích Khác"

    return "Tiện Ích Khác"


def parse_script_file(file_path, source_id, source_name, base_path, menu_map):
    fname = os.path.basename(file_path)
    ext = os.path.splitext(fname)[1].lower()
    rel_path = os.path.relpath(file_path, base_path).replace("\\", "/")
    rel_dir = os.path.dirname(rel_path)
    subfolder = "" if rel_dir == "." else rel_dir

    macro_name = ""
    script_cat = ""
    tooltip = ""
    button_text = ""
    rollout_title = ""
    description = ""
    commands = []

    menu_info = menu_map.get(fname.lower())
    if menu_info:
        tooltip = menu_info.get("title", "")
        if menu_info.get("code"):
            commands.append(menu_info["code"])

    # Đọc tối đa 40 dòng đầu để lấy nhanh metadata
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            head_lines = [f.readline() for _ in range(40)]
        content_sample = "".join(head_lines)

        m_mac = RE_MACRO.search(content_sample)
        if m_mac:
            macro_name = m_mac.group(1)
            commands.append(f"macro:{macro_name}")

        m_c = RE_CAT.search(content_sample)
        if m_c:
            script_cat = m_c.group(1).strip()

        m_t = RE_TOOLTIP.search(content_sample)
        if m_t:
            tooltip = tooltip or m_t.group(1).strip()

        m_b = RE_BTN.search(content_sample)
        if m_b:
            button_text = m_b.group(1).strip()

        m_r = RE_ROLLOUT.search(content_sample)
        if m_r:
            rollout_title = m_r.group(2).strip()
            commands.append(f"ui:{m_r.group(1)}")

        m_u = RE_UTILITY.search(content_sample)
        if m_u:
            rollout_title = rollout_title or m_u.group(2).strip()
            commands.append(f"util:{m_u.group(1)}")

        # Tìm dòng comment mô tả ngắn gọn
        for line in head_lines:
            l = line.strip()
            if l.startswith("--") and len(l) > 3 and not l.startswith("-----") and not l.startswith("===="):
                c = l.lstrip("- ").strip()
                if not any(ign in c.lower() for ign in ["copyright", "all rights", "(c)"]):
                    description = c
                    break
            elif l.startswith("#") and len(l) > 2 and not l.startswith("###"):
                c = l.lstrip("# ").strip()
                description = c
                break

    except Exception:
        pass

    category = categorize_maxscript(fname, subfolder, ext, source_name, script_cat, menu_info)
    feature_name = determine_feature_name(fname, subfolder, ext, source_name, menu_info, tooltip, rollout_title, description, macro_name)
    title_display = feature_name

    # Snippet chạy trong 3ds Max
    fwd_path = file_path.replace("\\", "/")
    if ext == ".py":
        run_command = f'python.ExecuteFile @" {fwd_path} "'
    else:
        run_command = f'fileIn @" {fwd_path} "'

    return {
        "file": fname,
        "featureName": feature_name,
        "title": title_display,
        "ext": ext,
        "source": source_name,
        "sourceId": source_id,
        "subfolder": subfolder,
        "relPath": rel_path,
        "fullPath": fwd_path,
        "category": category,
        "macro": macro_name,
        "buttonText": button_text,
        "tooltip": tooltip or rollout_title or description,
        "description": description or tooltip or f"Công cụ 3ds Max: {feature_name}",
        "commands": commands,
        "runCommand": run_command.replace(' @" ', ' @"').replace(' " ', '"'),
        "sizeBytes": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
        "modTime": os.path.getmtime(file_path) if os.path.exists(file_path) else 0
    }


def get_maxscript_list(force_reload=False):
    """Quét và tổng hợp toàn bộ script từ 2 nguồn (có cache bộ nhớ)."""
    global _CACHED_MAXSCRIPT_DATA, _LAST_SCAN_TIME
    now = time.time()
    if not force_reload and _CACHED_MAXSCRIPT_DATA is not None and (now - _LAST_SCAN_TIME < 60):
        return _CACHED_MAXSCRIPT_DATA

    menu_map = parse_skmenulist()
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
        for root, _, files in os.walk(base_dir):
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in VALID_EXTS:
                    full_p = os.path.join(root, f)
                    try:
                        item = parse_script_file(full_p, src_id, src_name, base_dir, menu_map)
                        all_items.append(item)
                        src_count += 1
                    except Exception:
                        pass
        source_stats[src_name] = src_count

    # Sắp xếp theo tên file
    all_items.sort(key=lambda x: x["file"].lower())

    # Thống kê danh mục
    cat_counts = {}
    for it in all_items:
        c = it["category"]
        cat_counts[c] = cat_counts.get(c, 0) + 1

    sorted_categories = sorted(cat_counts.keys(), key=lambda k: (-cat_counts[k], k))

    result = {
        "success": True,
        "message": f"Tổng hợp thành công {len(all_items)} scripts Maxscript & Python.",
        "totalFiles": len(all_items),
        "sources": source_stats,
        "categories": sorted_categories,
        "categoryCounts": cat_counts,
        "items": all_items
    }

    _CACHED_MAXSCRIPT_DATA = result
    _LAST_SCAN_TIME = now
    return result


def open_script_in_editor(file_path):
    """Mở file script bằng trình soạn thảo (VS Code nếu có, hoặc ứng dụng mặc định)."""
    if not os.path.exists(file_path):
        return False, f"File không tồn tại: {file_path}"
    try:
        # Thử mở bằng code trước nếu có
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
    res = get_maxscript_list(force_reload=True)
    t1 = time.time()
    print(f"Quet hoan tat trong {t1 - t0:.2f}s:")
    print("Success:", res["success"])
    print("Total:", res["totalFiles"])
    print("Sources:", res["sources"])
    print("Categories:", res["categoryCounts"])
    if res["items"]:
        print("Sample item 0:", res["items"][0]["file"], "->", res["items"][0]["category"])
