#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
scripts/select_by_grid.py
Hàm và CLI công cụ chọn đối tượng theo phạm vi trục (Grid / Axis) trong Autodesk Revit.
Hỗ trợ:
- Lọc theo trục X (1 trục kèm dung sai hoặc giữa 2 trục)
- Lọc theo trục Y (1 trục kèm dung sai hoặc giữa 2 trục)
- Lọc theo tầng (toàn bộ tầng, tầng hiện hành 'active', hoặc từng tầng cụ thể 'tang1', 'tang2', 'tum'...)
- Lọc theo Category (doors, windows, walls, columns, beams, floors, rooms, furniture, all...)
- Tự động highlight/chọn đối tượng trực tiếp trên giao diện Revit UI (Selection)
- Tùy chọn Zoom to elements, Isolate elements tạm thời
- Tái sử dụng linh hoạt dưới dạng hàm Python (import) hoặc dòng lệnh CLI
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.error

# Thiết lập encoding UTF-8
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Thêm thư mục gốc vào sys.path để import revit_cli
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

import revit_cli

DLL_PATH = os.path.join(PARENT_DIR, "bin", "Release", "net10.0-windows", "RevitScripts.dll")
if not os.path.exists(DLL_PATH):
    DLL_PATH = os.path.join(PARENT_DIR, "bin", "Release", "net10.0-windows", "DynamicConverter_DoorD7_v16.dll")


def select_elements_by_grid(
    grid_x=None,
    grid_y=None,
    grid_x_min=None,
    grid_x_max=None,
    grid_y_min=None,
    grid_y_max=None,
    min_x_mm=None,
    max_x_mm=None,
    min_y_mm=None,
    max_y_mm=None,
    level="all",
    category="all",
    tolerance_x_mm=1000.0,
    tolerance_y_mm=1500.0,
    margin_mm=100.0,
    set_selection=True,
    zoom_to=False,
    isolate=False,
    action="select",
    base_url=None,
    verbose=True
):
    """
    Hàm chọn đối tượng trong Revit theo phạm vi lưới trục.

    Tham số:
        grid_x (str hoặc list): Tên trục X. Ví dụ: "9", "9-10", ["9", "10"], "9,10".
        grid_y (str hoặc list): Tên trục Y. Ví dụ: "C", "B-D", ["B", "C"], "C".
        grid_x_min, grid_x_max (str): Tên trục X đầu và cuối.
        grid_y_min, grid_y_max (str): Tên trục Y đầu và cuối.
        min_x_mm, max_x_mm (float): Tọa độ X tùy chỉnh tính bằng milimet (nếu không dùng tên trục).
        min_y_mm, max_y_mm (float): Tọa độ Y tùy chỉnh tính bằng milimet (nếu không dùng tên trục).
        level (str): "all" (toàn bộ tầng), "active" (tầng của view đang mở), hoặc tên tầng ("tang1", "tang2", "tum", "mai"...).
        category (str hoặc list): Category cần lọc ("doors", "windows", "walls", "columns", "rooms", "all"...).
        tolerance_x_mm (float): Dung sai nếu chỉ truyền 1 trục X (mặc định 1000mm).
        tolerance_y_mm (float): Dung sai nếu chỉ truyền 1 trục Y (mặc định 1500mm).
        margin_mm (float): Khoảng nới rộng biên khi chọn giữa 2 trục (mặc định 100mm).
        set_selection (bool): Highlight/chọn trực tiếp các đối tượng trên màn hình Revit UI (mặc định True).
        zoom_to (bool): Zoom view đến các đối tượng được chọn (mặc định False).
        isolate (bool): Tạm thời cô lập các đối tượng trong view hiện hành (mặc định False).
        action (str): "select" (chọn), "delete" (xóa), "count_only" (chỉ đếm).
        verbose (bool): In thông tin ra màn hình console (mặc định True).

    Trả về:
        dict: Kết quả từ Revit Bridge (success, count, elementIds, elements, bounds_mm, grids).
    """
    if base_url is None:
        base_url = revit_cli.get_base_url()

    args_payload = {
        "setSelection": bool(set_selection),
        "zoomTo": bool(zoom_to),
        "isolate": bool(isolate),
        "action": str(action),
        "level": str(level) if level is not None else "all",
        "toleranceX_mm": float(tolerance_x_mm),
        "toleranceY_mm": float(tolerance_y_mm),
        "margin_mm": float(margin_mm)
    }

    # Xử lý grid_x
    if grid_x is not None:
        args_payload["gridX"] = grid_x
    if grid_x_min is not None:
        args_payload["gridXMin"] = str(grid_x_min)
    if grid_x_max is not None:
        args_payload["gridXMax"] = str(grid_x_max)

    # Xử lý grid_y
    if grid_y is not None:
        args_payload["gridY"] = grid_y
    if grid_y_min is not None:
        args_payload["gridYMin"] = str(grid_y_min)
    if grid_y_max is not None:
        args_payload["gridYMax"] = str(grid_y_max)

    # Xử lý tọa độ số nếu có
    if min_x_mm is not None and max_x_mm is not None:
        args_payload["minX_mm"] = float(min_x_mm)
        args_payload["maxX_mm"] = float(max_x_mm)
    if min_y_mm is not None and max_y_mm is not None:
        args_payload["minY_mm"] = float(min_y_mm)
        args_payload["maxY_mm"] = float(max_y_mm)

    # Xử lý category
    if category is not None:
        args_payload["categories"] = category

    payload = {
        "action": "execute_dynamic",
        "dllPath": DLL_PATH,
        "typeName": "RevitScript.SelectElementsByGrid",
        "methodName": "Run",
        "args": args_payload
    }

    req = urllib.request.Request(
        f"{base_url}/api/execute",
        data=json.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            data = json.loads(res.read().decode('utf-8'))
    except Exception as ex:
        err_res = {"success": False, "message": f"Không thể kết nối Revit Bridge: {ex}"}
        if verbose:
            print(f"[LỖI] {err_res['message']}")
        return err_res

    if verbose:
        print_summary(data)

    return data


def select_by_grid(*args, **kwargs):
    """Bí danh ngắn gọn cho select_elements_by_grid."""
    return select_elements_by_grid(*args, **kwargs)


def print_summary(data):
    """In bảng tóm tắt kết quả chọn đối tượng."""
    if not data.get("success"):
        print(f"[THẤT BẠI] {data.get('message')}")
        return

    count = data.get("count", 0)
    msg = data.get("message", "")
    grids = data.get("grids", {})
    bounds = data.get("bounds_mm", {})
    level = data.get("level", "Tất cả")
    elements = data.get("elements", [])

    print("=" * 75)
    print(f" KẾT QUẢ CHỌN ĐỐI TƯỢNG THEO PHẠM VI TRỤC ({count} đối tượng)")
    print("=" * 75)
    print(f"- Thông điệp: {msg}")
    print(f"- Trục X: {grids.get('gridX')} | Trục Y: {grids.get('gridY')}")
    if bounds:
        print(f"- Phạm vi hình học: X=[{bounds.get('minX')}, {bounds.get('maxX')}] mm | Y=[{bounds.get('minY')}, {bounds.get('maxY')}] mm")
    print(f"- Tầng áp dụng: {level}")
    print("-" * 75)

    if count == 0:
        print("  (Không tìm thấy đối tượng nào phù hợp trong phạm vi đã chọn)")
    else:
        # In tiêu đề bảng
        header = f"{'ID':<10} | {'Category':<15} | {'Family / Type':<30} | {'Mark':<8} | {'Tầng':<18} | {'Tọa độ (X, Y, Z)':<20}"
        print(header)
        print("-" * len(header))
        for e in elements[:50]:  # In tối đa 50 đối tượng đầu tiên
            name = f"{e.get('family', '')}: {e.get('type', '')}"
            if len(name) > 30:
                name = name[:27] + "..."
            coords = f"({e.get('x_mm')}, {e.get('y_mm')}, {e.get('z_mm')})"
            print(f"{e.get('id'):<10} | {e.get('category'):<15} | {name:<30} | {e.get('mark', ''):<8} | {e.get('level', ''):<18} | {coords:<20}")
        if count > 50:
            print(f"... và còn {count - 50} đối tượng khác.")
    print("=" * 75)


def main():
    parser = argparse.ArgumentParser(description="Chọn đối tượng trong phạm vi lưới trục Revit (từng tầng hoặc tất cả các tầng)")
    parser.add_argument("--grid-x", nargs="+", help="Tên trục X (vd: 9 hoặc 9 10)")
    parser.add_argument("--grid-y", nargs="+", help="Tên trục Y (vd: C hoặc B C hoặc B D)")
    parser.add_argument("--tolerance-x", type=float, default=1000.0, help="Dung sai nếu chỉ chỉ định 1 trục X (mm, mặc định 1000)")
    parser.add_argument("--tolerance-y", type=float, default=1500.0, help="Dung sai nếu chỉ chỉ định 1 trục Y (mm, mặc định 1500)")
    parser.add_argument("--margin", type=float, default=100.0, help="Độ nới rộng biên khi chọn giữa 2 trục (mm, mặc định 100)")
    parser.add_argument("--level", default="all", help="Lọc theo tầng: 'all', 'active' (view hiện hành), 'tang1', 'tang2', 'tang3', 'tang4', 'tum', 'mai'...")
    parser.add_argument("--cat", "--category", default="all", help="Category cần lọc: 'all', 'doors', 'windows', 'walls', 'columns', 'rooms', 'furniture'...")
    parser.add_argument("--no-select", action="store_true", help="Không tự động highlight/select trong Revit UI")
    parser.add_argument("--zoom", action="store_true", help="Tự động zoom view đến các đối tượng đã chọn")
    parser.add_argument("--isolate", action="store_true", help="Tạm thời isolate các đối tượng đã chọn trong view")
    parser.add_argument("--action", default="select", choices=["select", "delete", "count_only"], help="Hành động thực hiện")

    args = parser.parse_args()

    # Chuẩn hóa grid-x và grid-y nếu có nhiều giá trị
    grid_x = args.grid_x
    if grid_x and len(grid_x) == 1:
        grid_x = grid_x[0]

    grid_y = args.grid_y
    if grid_y and len(grid_y) == 1:
        grid_y = grid_y[0]

    select_elements_by_grid(
        grid_x=grid_x,
        grid_y=grid_y,
        level=args.level,
        category=args.cat,
        tolerance_x_mm=args.tolerance_x,
        tolerance_y_mm=args.tolerance_y,
        margin_mm=args.margin,
        set_selection=not args.no_select,
        zoom_to=args.zoom,
        isolate=args.isolate,
        action=args.action,
        verbose=True
    )


if __name__ == "__main__":
    main()
