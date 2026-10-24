# RevitAI Scripts: Chọn Đối Tượng Theo Phạm Vi Trục (Grid / Axis Selection)

Bộ công cụ tái sử dụng giúp chọn nhanh và highlight các đối tượng BIM trong Autodesk Revit theo phạm vi lưới trục và tầng.

---

## 1. Cấu trúc thư mục `scripts/`

- [`SelectElementsByGrid.cs`](file:///d:/Dropbox/_Documents/RevitAI/scripts/SelectElementsByGrid.cs): C# Engine chạy trực tiếp trong tiến trình Revit qua Revit Bridge API.
- [`select_by_grid.py`](file:///d:/Dropbox/_Documents/RevitAI/scripts/select_by_grid.py): Hàm Python và CLI wrapper có thể gọi từ dòng lệnh hoặc import vào code Python khác.
- [`__init__.py`](file:///d:/Dropbox/_Documents/RevitAI/scripts/__init__.py): Đóng gói thành Python package (`from scripts.select_by_grid import select_by_grid`).

---

## 2. Cách sử dụng qua dòng lệnh (CLI)

Chạy từ terminal / PowerShell trong thư mục dự án `d:\Dropbox\_Documents\RevitAI`:

### Ví dụ 1: Chọn tất cả cửa đi tại Trục C, giữa Trục 9 và 10 trên TẤT CẢ các tầng
```bash
python scripts/select_by_grid.py --grid-x 9 10 --grid-y C --tolerance-y 1500 --cat doors --level all
```

### Ví dụ 2: Chỉ chọn cửa đi tại Trục C, giữa Trục 9 và 10 riêng ở TẦNG 2
```bash
python scripts/select_by_grid.py --grid-x 9 10 --grid-y C --tolerance-y 1500 --cat doors --level tang2
```

### Ví dụ 3: Chọn tất cả đối tượng (tường, cột, sàn, cửa...) giữa Trục 1 - 3 và Trục A - C ở Tầng 1
```bash
python scripts/select_by_grid.py --grid-x 1 3 --grid-y A C --cat all --level tang1
```

### Ví dụ 4: Chọn trên tầng của View hiện hành đang mở trong Revit (`--level active`)
```bash
python scripts/select_by_grid.py --grid-x 5 8 --grid-y B D --level active
```

### Ví dụ 5: Tự động Zoom đến các đối tượng được chọn (`--zoom`)
```bash
python scripts/select_by_grid.py --grid-x 9 10 --grid-y C --cat doors --zoom
```

### Ví dụ 6: Tạm thời cô lập (Isolate) các đối tượng trong View hiện hành (`--isolate`)
```bash
python scripts/select_by_grid.py --grid-x 1 4 --grid-y A B --isolate
```

---

## 3. Cách gọi dưới dạng hàm trong Python

Có thể import trực tiếp vào bất kỳ script nào:

```python
from scripts.select_by_grid import select_by_grid

# 1. Chọn cửa trên trục C giữa trục 9 và 10 cho toàn bộ tầng
result = select_by_grid(
    grid_x=["9", "10"],
    grid_y="C",
    tolerance_y_mm=1500.0,
    category="doors",
    level="all",
    set_selection=True  # Tự động highlight trên giao diện Revit UI
)

print(f"Tổng số đối tượng: {result['count']}")
for elem in result["elements"]:
    print(f"ID {elem['id']}: {elem['family']} - {elem['type']} (Level: {elem['level']})")

# 2. Lấy danh sách ID để xử lý hàng loạt trong script khác
matched_ids = result["elementIds"]
```

---

## 4. Bảng tham số chi tiết

| Tham số CLI | Tham số hàm Python | Mặc định | Ý nghĩa |
| :--- | :--- | :---: | :--- |
| `--grid-x` | `grid_x` | `None` | Tên trục X. Có thể truyền 1 trục (`9`) hoặc 2 trục (`9 10` hoặc `["9", "10"]`). |
| `--grid-y` | `grid_y` | `None` | Tên trục Y. Có thể truyền 1 trục (`C`) hoặc 2 trục (`A C` hoặc `["A", "C"]`). |
| `--tolerance-x` | `tolerance_x_mm` | `1000.0` | Dung sai (mm) khi chỉ truyền 1 trục X (phạm vi $X \pm tol$). |
| `--tolerance-y` | `tolerance_y_mm` | `1500.0` | Dung sai (mm) khi chỉ truyền 1 trục Y (phạm vi $Y \pm tol$). |
| `--margin` | `margin_mm` | `100.0` | Độ nới rộng biên (mm) khi chọn giữa 2 trục. |
| `--level` | `level` | `"all"` | Tầng áp dụng: `"all"` (tất cả), `"active"` (view đang mở), hoặc tên tầng: `"tang1"`, `"tang2"`, `"tang3"`, `"tang4"`, `"tum"`, `"mai"`. |
| `--cat` / `--category` | `category` | `"all"` | Category cần lọc: `"doors"`, `"windows"`, `"walls"`, `"columns"`, `"rooms"`, `"floors"`, `"beams"`, `"all"`. |
| `--no-select` | `set_selection=False` | `True` | Nếu bật, chỉ lấy dữ liệu danh sách mà không highlight trên Revit UI. |
| `--zoom` | `zoom_to=True` | `False` | Tự động zoom view đến các đối tượng đã chọn. |
| `--isolate` | `isolate=True` | `False` | Tạm thời cô lập các đối tượng trong view hiện hành. |
| `--action` | `action` | `"select"` | Hành động: `"select"` (chọn), `"count_only"` (chỉ đếm), `"delete"` (xóa đối tượng). |
