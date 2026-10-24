import os
import sys
import re
import json
import shutil
import argparse
import subprocess
import urllib.request
import unicodedata
import revit_cli

sys.stdout.reconfigure(encoding='utf-8')

# Standard Layer Colors Dictionary (ACI Color Index 1 -> 8)
STANDARD_LAYER_COLORS = {
    # Nét cắt kết cấu & kiến trúc (Màu 7 - Trắng / White: Nét cắt chính 0.35-0.50mm)
    "A-WALL": 7,
    "A-WALL-CUT": 7,
    "S-COLS": 7,
    "S-BEAM": 7,
    "S-FRAM": 7,
    "S-FNDN": 7,
    "A-FLOR": 7,
    "A-FLOR-MCUT": 7,
    "A-DETL-WIDE": 7,
    
    # Cửa đi, khuôn cửa, thang, lan can, chữ ghi chú (Màu 2 - Vàng / Yellow: Nét vừa 0.20-0.25mm)
    "A-DOOR": 2,
    "A-DOOR-FRAM": 2,
    "S-STRS": 2,
    "S-STRS-MBND": 2,
    "A-FLOR-HRAL": 2,
    "A-FLOR-HRAL-MBND": 2,
    "A-ANNO-NOTE": 2,
    "G-ANNO-TEXT": 2,
    
    # Thiết bị vệ sinh, tag cửa, ký hiệu (Màu 3 - Xanh lá / Green: Nét thấy 0.15mm)
    "P-SANR-FIXT": 3,
    "A-DOOR-IDEN": 3,
    "A-GLAZ-IDEN": 3,
    "S-STRS-IDEN": 3,
    "S-STRS-ANNO": 3,
    "A-GENM": 3,
    "A-FURN": 3,
    
    # Cửa sổ, kính, vách kính (Màu 4 - Cyan / Xanh lơ: Nét kính 0.15-0.20mm)
    "A-GLAZ": 4,
    "A-DOOR-GLAZ": 4,
    "A-WALL-GLAZ": 4,
    
    # Kích thước, trục định vị, cao độ (Màu 1 - Đỏ / Red: Nét mảnh 0.09mm)
    "S-GRID": 1,
    "S-GRID-IDEN": 1,
    "G-ANNO-LEVL": 1,
    "A-ANNO-DIMS": 1,
    "A-ANNO-DIMS-75": 1,
    "A-ANNO-DIMS-100": 1,
    
    # Ký hiệu vết cắt / Section head (Màu 6 - Magenta / Tím: Nét ký hiệu 0.25mm)
    "G-ANNO-SYMB": 6,
    "A-ANNO-SYMB": 6,
    
    # Hatch vật liệu, nét chi tiết mảnh, CAD import (Màu 8 - Xám đậm / Gray: Nét siêu mảnh 0.05-0.09mm)
    "A-WALL-PATT": 8,
    "A-FLOR-PATT": 8,
    "S-COLS-PATT": 8,
    "A-FLOR-LEVL": 8,
    "A-DETL": 8,
    "A-DETL-THIN": 8,
    "A-DETL-GENF": 8,
    "G-IMPT": 8,
    
    # Mặc định
    "0": 7,
    "Defpoints": 7
}

# Wildcard rules for layer colors
WILDCARD_COLOR_RULES = [
    ("*PATT*", 8),
    ("*HATCH*", 8),
    ("*DETL-THIN*", 8),
    ("*IMPT*", 8),
    ("*DIMS*", 1),
    ("*GRID*", 1),
    ("*LEVL*", 1),
    ("*GLAZ*", 4),
    ("*DOOR*", 2),
    ("*STRS*", 2),
    ("*HRAL*", 2),
    ("*NOTE*", 2),
    ("*TEXT*", 2),
    ("*SANR*", 3),
    ("*IDEN*", 3),
    ("*FURN*", 3),
    ("*SYMB*", 6),
    ("*WALL*", 7),
    ("*COLS*", 7),
    ("*BEAM*", 7),
    ("*FRAM*", 7),
    ("*FLOR*", 7),
    ("*FNDN*", 7)
]

def normalize_str(text):
    if not text:
        return ""
    norm = unicodedata.normalize('NFKD', str(text))
    return "".join(c for c in norm if not unicodedata.combining(c)).lower().strip()

def to_acad_unicode(s):
    """Chuyển đổi chuỗi tiếng Việt có dấu thành mã Unicode chuẩn AutoCAD \\U+XXXX"""
    res = []
    for char in s:
        cp = ord(char)
        if cp > 127:
            res.append(f'\\U+{cp:04X}')
        else:
            res.append(char)
    return ''.join(res)

def get_browser_groups():
    """Lấy danh sách các Group trong Project Browser từ Revit"""
    base_url = revit_cli.get_base_url()
    payload = {
        "action": "execute_dynamic",
        "dllPath": r"D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_DoorD7_v16.dll",
        "typeName": "RevitScript.GetProjectBrowserGroups",
        "methodName": "Run",
        "args": {}
    }
    try:
        req = urllib.request.Request(
            f"{base_url}/api/execute",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw_groups = data.get("groups") or data.get("Groups") or []
            valid_groups = []
            for g in raw_groups:
                gname = g.get("groupName") or g.get("GroupName") or ""
                vlist = g.get("views") or g.get("Views") or []
                # Chỉ lọc các group view 2D có thể xuất bản vẽ DWG
                if not any(k in gname for k in ["3D", "Schedule", "Legend"]):
                    valid_groups.append({
                        "name": gname,
                        "views": vlist
                    })
            return valid_groups
    except Exception as e:
        print(f"[ERROR] Không lấy được danh sách group từ Revit: {e}")
        return []

def resolve_group_views(group_queries, all_groups):
    """Tìm tất cả các View IDs khớp với các từ khóa Group do người dùng cung cấp"""
    matched_groups = []
    selected_view_ids = []

    for query in group_queries:
        q_raw = str(query).strip()
        q_norm = normalize_str(q_raw)

        # Nếu là số thứ tự: ví dụ "1", "2"
        if q_raw.isdigit():
            idx = int(q_raw)
            if 1 <= idx <= len(all_groups):
                g = all_groups[idx - 1]
                if g["name"] not in [mg["name"] for mg in matched_groups]:
                    matched_groups.append(g)
            continue

        # Tìm theo chuỗi tên
        q_clean = q_norm.replace(" ", "").replace("_", "").replace("-", "")
        for g in all_groups:
            g_name = g["name"]
            g_norm = normalize_str(g_name)
            g_clean = g_norm.replace(" ", "").replace("_", "").replace("-", "")

            # Khớp tên chính xác hoặc chứa từ khóa (kể cả viết liền không dấu)
            if (q_norm in g_norm or 
                q_clean in g_clean or 
                all(term in g_norm for term in q_norm.split())):
                if g_name not in [mg["name"] for mg in matched_groups]:
                    matched_groups.append(g)

    for g in matched_groups:
        for v in g["views"]:
            vid = v.get("id") or v.get("Id")
            if vid and vid not in selected_view_ids:
                selected_view_ids.append(vid)

    return matched_groups, selected_view_ids

def export_views_vertical(output_name="TONG_HOP_HANG_DOC.dwg", gap_mm=6000.0, view_ids=None, group_queries=None, title_height=600.0):
    if not output_name.lower().endswith(".dwg"):
        output_name += ".dwg"

    base_url = revit_cli.get_base_url()
    all_groups = get_browser_groups()

    print("=" * 65)
    print(" XUẤT CÁC VIEW ĐANG CHỌN THÀNH 1 FILE DWG XẾP HÀNG DỌC")
    print("=" * 65)

    # 1. Xác định danh sách view_ids nếu người dùng chỉ định qua --group
    if group_queries:
        matched_groups, resolved_ids = resolve_group_views(group_queries, all_groups)
        if matched_groups:
            print(f"[OK] Đã nhận diện {len(matched_groups)} Group được chọn:")
            for mg in matched_groups:
                print(f"  + Group '{mg['name']}': {len(mg['views'])} views")
            view_ids = resolved_ids
        else:
            print(f"[CẢNH BÁO] Không tìm thấy group nào khớp với: {group_queries}")
            return False

    # 2. Nếu chưa có view_ids, thử gọi Revit xem người dùng có chọn trực tiếp view con không
    if not view_ids:
        payload_test = {
            "action": "execute_dynamic",
            "dllPath": r"D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_DoorD7_v16.dll",
            "typeName": "RevitScript.ExportSelectedViewsVerticalDwg",
            "methodName": "Run",
            "args": {
                "gapMm": float(gap_mm),
                "viewIds": None
            }
        }

        try:
            req = urllib.request.Request(
                f"{base_url}/api/execute",
                data=json.dumps(payload_test).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"[ERROR] Lỗi kết nối tới Revit Bridge: {e}")
            return False

        # Nếu Revit không thấy view con nào được chọn (thường do click vào Folder Header)
        if not data.get("success"):
            print("\n[CHÚ Ý] Trong Revit, khi click vào tiêu đề thư mục (Group header) như 'Floor Plans' hay 'Sections',")
            print("        Revit API không tự bôi đen các view con bên trong.")
            print("\n" + "=" * 65)
            print(" DANH SÁCH CÁC GROUP VIEW TRONG PROJECT BROWSER:")
            print("=" * 65)
            for idx, g in enumerate(all_groups, 1):
                print(f"  [{idx:2d}] {g['name']:<35} ({len(g['views']):2d} views)")
            print("=" * 65)

            try:
                user_choice = input("\n👉 Nhập số thứ tự các group bạn muốn in (ví dụ: 7, 8 hoặc 'all'): ").strip()
            except (EOFError, KeyboardInterrupt):
                user_choice = ""

            if not user_choice:
                print("[HỦY BỎ] Không có group nào được chọn. Thoát chương trình.")
                return False

            if user_choice.lower() == 'all':
                view_ids = []
                for g in all_groups:
                    for v in g["views"]:
                        vid = v.get("id") or v.get("Id")
                        if vid and vid not in view_ids:
                            view_ids.append(vid)
            else:
                indices = re.findall(r'\d+', user_choice)
                matched_groups, view_ids = resolve_group_views(indices, all_groups)
                print(f"\n[OK] Đã chọn {len(matched_groups)} Group ({len(view_ids)} views).")

            if not view_ids:
                print("[ERROR] Không tìm thấy view nào trong các group đã chọn.")
                return False

    # 3. Xuất DWG từng view từ Revit
    payload = {
        "action": "execute_dynamic",
        "dllPath": r"D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_DoorD7_v16.dll",
        "typeName": "RevitScript.ExportSelectedViewsVerticalDwg",
        "methodName": "Run",
        "args": {
            "gapMm": float(gap_mm),
            "viewIds": [int(v) for v in view_ids] if view_ids else None
        }
    }

    try:
        req = urllib.request.Request(
            f"{base_url}/api/execute",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[ERROR] Lỗi xuất view từ Revit Bridge: {e}")
        return False

    if not data.get("success"):
        print(f"[CHÚ Ý] {data.get('message', 'Không thể xuất view.')}")
        return False

    views = data.get("views", [])
    if not views:
        print("[ERROR] Không có view nào được xuất.")
        return False

    print(f"\n[OK] Đã xuất thành công {len(views)} view từ Revit:")
    for v in views:
        print(f"  {v['index']}. {v['name']} (ID {v['id']}): Rộng={v['width']:.0f}mm, Cao={v['height']:.0f}mm -> Y_Offset={v['yOffset']:.0f}mm")

    return assemble_vertical_dwg(data, output_name=output_name, title_height=title_height)

def assemble_vertical_dwg(data, output_name="TONG_HOP_HANG_DOC.dwg", title_height=600.0):
    if not output_name.lower().endswith(".dwg"):
        output_name += ".dwg"

    views = data.get("views", [])
    if not views:
        print("[ERROR] Không có view nào để gộp.")
        return False

    export_folder = data.get("exportFolder")
    master_dwg_temp = os.path.join(export_folder, output_name)

    # 4. Phân loại Views thành 2 Cột: Cột Mặt Bằng (Trái) & Cột Mặt Cắt/Chi Tiết (Phải)
    plan_views = []
    section_views = []

    for v in views:
        vname_norm = normalize_str(v.get("name", ""))
        if any(k in vname_norm for k in ["mat bang", "tang", "mai", "ap mai", "tum", "floor", "ceiling", "roof"]):
            plan_views.append(v)
        else:
            section_views.append(v)

    # Tự động tính toán tọa độ chèn (TargetX, TargetY) và vị trí tiêu đề (TitleX, TitleY)
    Y_STEP_PLAN = 35000.0     # Bước nhảy mặt bằng: 35m (đảm bảo thoáng và đều, không bị thưa 140m)
    Y_STEP_SECTION = 32000.0  # Bước nhảy mặt cắt: 32m
    X_COL2 = 65000.0          # Cột mặt cắt đặt lệch sang phải 65m

    placed_views = []

    if len(plan_views) > 0 and len(section_views) > 0:
        # Sắp xếp 2 cột song song
        print(f"\n[BỐ CỤC 2 CỘT] Cột Trái: {len(plan_views)} Mặt bằng | Cột Phải: {len(section_views)} Mặt cắt")
        
        # Cột 1: Mặt bằng
        for i, v in enumerate(plan_views):
            y_off = -i * Y_STEP_PLAN
            v["targetX"] = 0.0
            v["targetY"] = y_off
            v["titleX"] = 20000.0  # Căn giữa bề rộng nhà (trục 1 đến 11 ~38m)
            v["titleY"] = y_off - 8000.0
            placed_views.append(v)

        # Cột 2: Mặt cắt (song song bên phải)
        for j, v in enumerate(section_views):
            y_off = -j * Y_STEP_SECTION
            v["targetX"] = X_COL2
            v["targetY"] = y_off
            w = v.get("width") or 40000.0
            v["titleX"] = X_COL2 + (w * 0.5)
            v["titleY"] = y_off - 5000.0
            placed_views.append(v)
    else:
        # 1 cột duy nhất
        all_list = plan_views if plan_views else section_views
        step = Y_STEP_PLAN if plan_views else Y_STEP_SECTION
        for i, v in enumerate(all_list):
            y_off = -i * step
            v["targetX"] = 0.0
            v["targetY"] = y_off
            w = v.get("width") or 38000.0
            v["titleX"] = w * 0.5
            v["titleY"] = y_off - 6000.0
            placed_views.append(v)

    # File cơ sở là view đầu tiên
    base_file = placed_views[0]["filePath"]
    if not os.path.exists(base_file):
        print(f"[ERROR] File cơ sở không tồn tại: {base_file}")
        return False

    shutil.copyfile(base_file, master_dwg_temp)

    # 5. Xây dựng kịch bản AutoLISP cho AutoCAD Core Console
    import ctypes
    def get_short_path(path):
        try:
            buf = ctypes.create_unicode_buffer(500)
            ctypes.windll.kernel32.GetShortPathNameW(path, buf, 500)
            return buf.value or path
        except:
            return path

    scr_lines = [
        "(vl-load-com)",
        "(defun c:ASSEMBLE ( / ss i ent ed)",
        "  (setvar \"FILEDIA\" 0)",
        "  (setvar \"CMDECHO\" 1)"
    ]

    # Chèn các view còn lại (từ view thứ 2 trở đi)
    for v in placed_views[1:]:
        sp = get_short_path(v["filePath"]).replace("\\", "/")
        tx = v["targetX"]
        ty = v["targetY"]
        scr_lines.append(f'  (command "_.-INSERT" "*{sp}" (list {tx:.1f} {ty:.1f} 0.0) 1.0 0.0)')

    # Thiết lập Text Style chuẩn Unicode (Arial)
    scr_lines.append('  (command "_.-STYLE" "UNICODE_TITLE" "arial.ttf" "0" "1.0" "0" "_N" "_N")')

    # Thêm tiêu đề tên cho tất cả các view bằng mã Unicode \\U+XXXX
    for v in placed_views:
        encoded_title = to_acad_unicode(v["name"])
        tx = v["titleX"]
        ty = v["titleY"]
        scr_lines.append(f'  (command "_.-TEXT" "_S" "UNICODE_TITLE" "_J" "_MC" (list {tx:.1f} {ty:.1f} 0.0) {title_height:.1f} 0.0 "{encoded_title}")')

    # Ép tất cả đối tượng về ByLayer (màu 256)
    scr_lines.append('  (if (setq ss (ssget "X"))')
    scr_lines.append('    (repeat (setq i (sslength ss))')
    scr_lines.append('      (setq ent (ssname ss (setq i (1- i))))')
    scr_lines.append('      (setq ed (entget ent))')
    scr_lines.append('      (if (assoc 62 ed)')
    scr_lines.append("        (entmod (subst '(62 . 256) (assoc 62 ed) ed))")
    scr_lines.append('      )')
    scr_lines.append('    )')
    scr_lines.append('  )')

    # Áp bảng màu Layer chuẩn
    scr_lines.append('  (command "_.-LAYER"')
    for pattern, col in WILDCARD_COLOR_RULES:
        scr_lines.append(f'    "_C" "{col}" "{pattern}"')
    for lay, col in STANDARD_LAYER_COLORS.items():
        scr_lines.append(f'    "_C" "{col}" "{lay}"')
    scr_lines.append('    ""')
    scr_lines.append('  )')

    # Zoom Extents và QSave
    scr_lines.append('  (command "_.ZOOM" "_E")')
    scr_lines.append('  (command "_.QSAVE")')
    scr_lines.append('  (princ "\\n*** ASSEMBLE_SUCCESS ***\\n")')
    scr_lines.append(')')
    scr_lines.append('(c:ASSEMBLE)')
    scr_lines.append('_QUIT')
    scr_lines.append('_Y')

    scr_path = os.path.join(export_folder, "assemble_vertical.scr")
    with open(scr_path, "w", encoding="utf-8") as f:
        f.write("\n".join(scr_lines) + "\n")

    # 6. Chạy AutoCAD Core Console
    accoreconsole = r"C:\Program Files\Autodesk\AutoCAD 2022\accoreconsole.exe"
    if not os.path.exists(accoreconsole):
        print(f"[WARNING] Không tìm thấy accoreconsole tại: {accoreconsole}")
        print(f"File tạm đã tạo: {master_dwg_temp}")
        return True

    print("\nĐang chạy AutoCAD Core Console để gộp hàng dọc và set màu layer...")
    cmd = [accoreconsole, "/i", master_dwg_temp, "/s", scr_path]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="ignore", timeout=120)
        log_path = os.path.join(export_folder, "assemble_log.txt")
        with open(log_path, "w", encoding="utf-8") as lf:
            lf.write(proc.stdout)
    except subprocess.TimeoutExpired:
        print("[ERROR] AutoCAD Core Console bị quá thời gian (Timeout).")
        return False

    if not os.path.exists(master_dwg_temp):
        print("[ERROR] Quá trình gộp DWG thất bại.")
        return False

    final_size_mb = os.path.getsize(master_dwg_temp) / (1024.0 * 1024.0)
    print(f"\n[THÀNH CÔNG] Đã tạo file DWG tổng hợp: {output_name} ({final_size_mb:.2f} MB)")

    # 7. Đồng bộ file đầu ra vào Project và Desktop
    try:
        project_dir = r"D:\Dropbox\_Documents\_KIEN TRUC 2026\CAX"
        if os.path.exists(project_dir):
            dest_project = os.path.join(project_dir, output_name)
            shutil.copyfile(master_dwg_temp, dest_project)
            print(f" -> Đã lưu vào Project: {dest_project}")
    except Exception as ex_p:
        print(f" [Note] Bỏ qua sync vào Project CAX: {ex_p}")

    try:
        desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        if os.path.exists(desktop_dir):
            dest_desktop = os.path.join(desktop_dir, output_name)
            shutil.copyfile(master_dwg_temp, dest_desktop)
            print(f" -> Đã copy ra Desktop: {dest_desktop}")
    except Exception as ex_d:
        print(f" [Note] Bỏ qua sync ra Desktop: {ex_d}")

    print("\n" + "=" * 65)
    print(" BẢNG MÀU LAYER THEO TIÊU CHUẨN ĐÃ THIẾT LẬP:")
    print("=" * 65)
    print(" - Màu 7 (White)   : Tường, Cột, Dầm, Sàn (Nét cắt đậm chính 0.35-0.50mm)")
    print(" - Màu 2 (Yellow)  : Cửa đi, Cầu thang, Lan can, Ghi chú (Nét vừa 0.20-0.25mm)")
    print(" - Màu 3 (Green)   : Thiết bị vệ sinh, Tag cửa, Nội thất (Nét thấy 0.15mm)")
    print(" - Màu 4 (Cyan)    : Cửa sổ, Kính, Vách kính (Nét kính mảnh 0.15-0.20mm)")
    print(" - Màu 1 (Red)     : Trục định vị, Dim kích thước, Cao độ (Nét mảnh 0.09mm)")
    print(" - Màu 6 (Magenta) : Ký hiệu vết cắt, Khung tên (Nét ký hiệu 0.25mm)")
    print(" - Màu 8 (Gray)    : Hatch gạch, Hatch bê tông, Nét phụ (Nét siêu mảnh 0.05-0.09mm)")
    print("=" * 65)

    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export selected views in Project Browser to a single vertical DWG with standard layer colors")
    parser.add_argument("--name", default="TONG_HOP_HANG_DOC.dwg", help="Tên file DWG đầu ra (mặc định: TONG_HOP_HANG_DOC.dwg)")
    parser.add_argument("--gap", type=float, default=6000.0, help="Khoảng cách giữa các view theo chiều dọc tính bằng mm (mặc định: 6000)")
    parser.add_argument("--views", nargs="*", type=int, help="Danh sách View ID cụ thể")
    parser.add_argument("--group", "-g", nargs="*", type=str, help="Tên hoặc từ khóa các Group trong Project Browser (ví dụ: --group floor section)")
    parser.add_argument("--list-groups", action="store_true", help="Liệt kê danh sách tất cả các Group trong Project Browser rồi thoát")
    parser.add_argument("--title-height", type=float, default=600.0, help="Chiều cao chữ tiêu đề tên view tính bằng mm (mặc định: 600)")
    args = parser.parse_args()

    if args.list_groups:
        groups = get_browser_groups()
        print("=" * 65)
        print(" DANH SÁCH CÁC GROUP VIEW TRONG PROJECT BROWSER:")
        print("=" * 65)
        for i, g in enumerate(groups, 1):
            print(f"[{i:2d}] {g['name']:<35} ({len(g['views']):2d} views)")
            for v in g["views"]:
                vid = v.get("id") or v.get("Id")
                vname = v.get("name") or v.get("Name")
                print(f"       - ID {vid}: {vname}")
        print("=" * 65)
        sys.exit(0)

    export_views_vertical(output_name=args.name, gap_mm=args.gap, view_ids=args.views, group_queries=args.group, title_height=args.title_height)
