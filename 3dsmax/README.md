# 🤖 3ds Max AI Copilot Bridge & Chatbot

Hệ thống tích hợp AI Copilot dành riêng cho **Autodesk 3ds Max** (hỗ trợ toàn diện các phiên bản 3ds Max 2020, 2021, 2022, 2024+), tương tự kiến trúc RevitAI, cho phép bạn và AI (Antigravity) điều khiển, truy vấn và tự động hóa 3ds Max từ xa.

---

## 🌟 Tính năng chính

1. **Giao diện Chatbot tích hợp trực tiếp trong 3ds Max (Dockable / Floating UI)**
   - Viết bằng PySide (Qt) với Dark Theme đồng bộ 3ds Max.
   - Hiển thị trạng thái kết nối `🟢 Online`, cổng Bridge, thông tin scene.
   - Thanh công cụ thao tác nhanh:
     - 🔍 **Inspect**: Thống kê số lượng đối tượng, đa giác, vật liệu, render engine.
     - 📸 **Render Preview**: Kết xuất nhanh góc nhìn hiện tại ra ảnh.
     - 💡 **3-Point Light**: Tự động dựng hệ thống chiếu sáng chuẩn studio (Key, Fill, Rim).
     - 🧹 **Clean Scene**: Dọn dẹp layer rác, giải phóng bộ nhớ texture và RAM.
   - Khung hội thoại tương tác trực tiếp bằng ngôn ngữ tự nhiên hoặc gõ trực tiếp lệnh MAXScript.

2. **HTTP Bridge Server an toàn trên Main Thread**
   - Lắng nghe tại cổng mặc định `http://127.0.0.1:8096` (tránh xung đột với Revit 8088/8090 và AutoCAD 8089).
   - Tự động điều phối mọi thao tác can thiệp scene qua hàng đợi an toàn trên luồng chính (`QTimer` event loop), không bao giờ gây treo hoặc crash 3ds Max.

3. **REST API & MCP Protocol**
   - `GET /api/status`: Lấy phiên bản 3ds Max, file đang mở, đơn vị hệ thống, renderer, viewport.
   - `GET /api/scene`: Liệt kê cây đối tượng, layer, vật liệu, poly/vertex count, tọa độ.
   - `POST /api/execute`: Chạy bất kỳ đoạn mã **MAXScript** hoặc **Python** nào và trả về kết quả ngay lập tức.
   - `POST /api/action`: Thực hiện các lệnh dựng hình, camera, đèn, xuất/nhập file (FBX, OBJ, glTF).
   - `POST /api/chat`: Xử lý prompt thông minh cho chatbot.
   - `POST /mcp`: Tương thích Model Context Protocol cho AI Agent tool-calling.

4. **CLI Client mạnh mẽ (`max_cli.py`)**
   - Điều khiển toàn bộ 3ds Max trực tiếp từ Terminal hoặc script Python bên ngoài.

---

## 🚀 Kích hoạt và Sử dụng

### 1. Kích hoạt ngay lập tức trong phiên 3ds Max đang mở
Trong 3ds Max (ví dụ phiên bản 2022 đang chạy của bạn):
- **Cách 1 (Khuyên dùng)**: Mở **MAXScript Listener** (`F11`) và chạy 1 dòng sau:
  ```maxscript
  filein @"d:\Dropbox\_Documents\RevitAI\3dsmax\max_bridge_startup.ms"
  ```
- **Cách 2**: Trên menu 3ds Max, chọn `Scripting` -> `Run Script...` -> trỏ tới file `d:\Dropbox\_Documents\RevitAI\3dsmax\max_bridge_startup.ms`.
- **Cách 3 (Thêm nút bấm vào Toolbar)**:
  - Vào `Customize` -> `Customize User Interface` -> Tab `Toolbars`.
  - Mục `Category` chọn **"AI Tools"**.
  - Kéo biểu tượng **"AI Chatbot"** thả vào bất kỳ thanh công cụ nào trên màn hình 3ds Max để bật/tắt chatbot bất cứ lúc nào!

### 2. Tự động khởi động cùng 3ds Max
Script cài đặt đã tự động gắn hook vào thư mục `startup` của các phiên bản 3ds Max (2020, 2021, 2022, 2024). Từ các lần mở 3ds Max tiếp theo, Bridge và Chatbot sẽ tự động khởi chạy ngầm.

---

## 💻 Sử dụng CLI (`max_cli.py`)

Từ Terminal tại thư mục `d:\Dropbox\_Documents\RevitAI\3dsmax`:

```bash
# Kiểm tra trạng thái 3ds Max & scene hiện tại
python max_cli.py status

# Xem danh sách đối tượng & vật liệu trong scene
python max_cli.py scene

# Chạy lệnh MAXScript bất kỳ
python max_cli.py execute "box length:50 width:50 height:50 pos:[0,0,0]"
python max_cli.py execute "select $*"
python max_cli.py execute "format 'Total polys: %\n' (for o in objects collect getNumFaces o)"

# Chạy mã Python trực tiếp
python max_cli.py execute-py "import pymxs; print(pymxs.runtime.maxFileName)"

# Tạo nhanh vật thể cơ bản
python max_cli.py create Box 0 0 0 MyBox
python max_cli.py create Teapot 100 0 0

# Tạo hệ thống đèn 3-Point Light
python max_cli.py create-lights

# Tạo Camera
python max_cli.py create-camera 0 -300 200

# Render khung nhìn hiện tại ra ảnh
python max_cli.py render my_render.png 1920 1080

# Xuất mô hình ra file FBX
python max_cli.py export "D:\export_model.fbx"

# Dọn dẹp layer rác và giải phóng bộ nhớ
python max_cli.py clean

# Tương tác với Chatbot
python max_cli.py chat "Thống kê scene hiện tại giúp tôi"
```

---

## 📁 Cấu trúc tập tin

### Lịch sử lệnh trong ô chat

Nhấn **↑** để lấy lệnh trước, **↓** để đi tới lệnh mới hơn và trở lại nội dung
đang gõ. Lệnh chỉ chạy khi nhấn Enter hoặc Gửi. Lưu tối đa 200 lệnh trong
phiên panel hiện tại, bỏ qua lệnh trùng liên tiếp.

Khi gửi lệnh, panel hiện thanh loading và số giây chờ: `Đang chuẩn hoá lệnh`
rồi `Đang thực hiện trong Max`. Nút Gửi đổi thành `Chờ` để tránh gửi trùng;
vẫn có thể soạn nội dung tiếp theo. Loading tự tắt khi xong hoặc có lỗi.

Nút `▶ Chạy Qwen` khởi động Ollama cục bộ nếu chưa chạy và nạp model 4B
vào GPU. Nút đổi thành `Đang nạp Qwen...` trong lúc chờ rồi báo kết quả trong
chat; thao tác chạy trên worker để không chặn giao diện Max.

### Thay khối đang chọn bằng cylinder, half cylinder hoặc box bbox

Chọn đúng **một khối mesh** rồi nhập vào panel AI:

```text
tạo cylinder fit trục X
tạo cylinder fit trục Y
tạo cylinder fit trục Z
tạo box từ bbox
tạo box
tạo half cylinder trục X
tạo half cylinder trục Y
tạo half cylinder trục Z
tạo cylinder fit trục X bỏ nắp trên và dưới
tạo half cylinder trục Y bỏ nắp trên và dưới
tạo box từ bbox bỏ nắp trên và dưới
```

Mặc định **xoá khối gốc sau khi tạo thành công**, giữ vật liệu và màu wire của
khối gốc. Một lần Ctrl+Z xoá khối mới và khôi phục khối gốc. Thêm `giữ khối gốc`
vào câu lệnh nếu muốn giữ cả hai.

Khối mới luôn được **convert sang Editable Poly** và mặc định **giữ nắp**.
`tạo cylinder fit z` tạo khối kín. Chỉ xoá nắp khi có yêu cầu rõ:

| Cụm từ trong lệnh | Kết quả |
| :--- | :--- |
| `không nắp`, `không nắp trên/dưới`, `bỏ nắp trên và dưới` | Xoá cả hai nắp |
| `không nắp trên` | Chỉ xoá nắp trên |
| `không nắp dưới` | Chỉ xoá nắp dưới |
| `giữ nắp` hoặc không nhắc tới nắp | Giữ nắp |

Cylinder xoá nắp tròn, half cylinder xoá nắp bán nguyệt, box xoá mặt tương ứng
theo Z. Các mặt bên được giữ lại. Với cylinder trục X/Y, trên/dưới tương ứng
hai đầu dương/âm dọc trục đã chọn.
Cũng có thể chọn khối rồi nhập riêng `bỏ nắp trên và dưới`. Khối tạo bởi bridge
ghi nhớ hướng nắp theo local Z, nên vẫn dùng được khi đã xoay khối. Với khối
khác, thêm `trục X`, `trục Y` hoặc `trục Z` để chỉ định hai mặt đầu theo trục
thế giới; nếu không có thông tin hướng thì mặc định Z.

Nếu bỏ trục, mặc định là Z. Cylinder bao khối theo trục thế giới đã chọn,
đáy và đỉnh khớp bounding box dọc trục đó. Bán kính tính từ các đỉnh mesh
quanh tâm bounding box trong mặt phẳng vuông góc; mặc định 32 cạnh, được bù bán kính
để mặt bên không cắt vào khối. Kết quả được chọn sau khi tạo.

Box khớp bounding box theo các trục thế giới, kể cả khi khối gốc có xoay/scale.
Half cylinder là cylinder có slice 180°, bao mesh từ một mặt phẳng ở mép bbox:

| Trục dọc | Mặt phẳng đáy của nửa đường tròn | Hướng phần cong |
| :--- | :--- | :--- |
| X | Z nhỏ nhất của bbox | +Z |
| Y | X nhỏ nhất của bbox | +X |
| Z | Y nhỏ nhất của bbox | +Y |

Bán kính half cylinder được tính từ mặt phẳng này để bao khối, nên bbox của
half cylinder có thể lớn hơn bbox gốc theo hai trục ngang.

API `POST /api/action`:

```json
{"action": "fit_cylinder", "params": {"axis": "X", "sides": 32, "delete_source": true}}
{"action": "fit_half_cylinder", "params": {"axis": "Y", "delete_source": true}}
{"action": "box_from_bbox", "params": {"delete_source": true}}
{"action": "fit_cylinder", "params": {"axis": "X", "remove_caps": true}}
{"action": "remove_caps", "params": {}}
{"action": "fit_cylinder", "params": {"axis": "Z", "remove_caps": "top"}}
```

Python trong Max: `max_bridge.create_fitted_cylinder("Y")`.
Hoặc `max_bridge.create_fitted_half_cylinder("X")`, `max_bridge.create_bbox_box()`.
Số cạnh hợp lệ: 12–512; half cylinder làm tròn lên số chẵn.
Kích thước dùng đơn vị hệ thống của scene.

### Chuẩn hoá prompt bằng Qwen cục bộ

`prompt_normalizer.py` gọi Qwen3.5 4B Q4_K_M qua Ollama tại `127.0.0.1:11434`,
tắt thinking, context 2048 và giữ model trong bộ nhớ 30 phút sau lần dùng cuối.
Cấu hình ở `qwen_normalizer.json`; `base_url` chỉ chấp nhận loopback HTTP.
Không gửi câu lệnh hoặc dữ liệu scene tới VPS khi dùng cấu hình này.
Muốn trở lại VPS thì bỏ `base_url` và dùng model có sẵn ở VPS cùng cấu hình SSH.

Máy Windows hiện tại dùng GTX 1080 Ti với backend Vulkan: CUDA mới không tương
thích driver 561.17. Ollama nằm ở `%LOCALAPPDATA%\Programs\Ollama`, model ở
`%USERPROFILE%\.ollama\models`. `Ollama Local.vbs` trong Startup chạy server ẩn
khi đăng nhập, chỉ đặt biến môi trường Vulkan/CUDA cho tiến trình Ollama.
Các lệnh ngắn rõ ràng như `tạo box`, `vẽ box`, `tạo hộp` được xử lý ngay tại máy,
không chờ VPS; mặc định tạo box từ bbox của một khối đang chọn.

Ô chat và `POST /api/chat` chuẩn hoá câu lệnh trước khi thực thi. Model chỉ trả
JSON gồm loại thao tác và trục, không sinh MAXScript/Python để chạy. Bridge
kiểm tra action hợp lệ, lấy yêu cầu nắp, số cạnh và giữ/xoá khối gốc từ câu gốc.
Mặc định Z, 32 cạnh, giữ nắp và xoá khối gốc sau khi tạo thành công.

Ví dụ: `tao cylider fit z khong nap` được nhận là cylinder trục Z, bỏ cả hai nắp.
Lời gọi model chạy trên worker để không chặn giao diện Max. Nếu selection thay đổi
trong lúc chờ thì lệnh dừng và yêu cầu chọn lại; model lỗi/timeout thì dùng bộ
nhận diện cục bộ và báo trong kết quả. Các lệnh ngoài nhóm fit/bỏ nắp tiếp tục
được xử lý bởi chatbot hiện có. Có thể tắt Qwen bằng `enabled: false`.

Nạp cập nhật mà giữ panel/lịch sử: `python 3dsmax/reload_chat_commands.py`.
Kiểm tra parser/fallback: `python 3dsmax/test_prompt_normalizer.py`.

Kiểm tra tích hợp trong Max đang mở: `python 3dsmax/test_fit_primitives_live.py`.
Script nạp các hàm mới, tạo khối thử, kiểm tra fit và undo rồi dọn khối thử,
khôi phục selection ban đầu. Chạy khi Max đang rảnh.

| Tập tin | Chức năng |
| :--- | :--- |
| [`max_bridge.py`](file:///d:/Dropbox/_Documents/RevitAI/3dsmax/max_bridge.py) | Bridge Server (HTTP) & Giao diện PySide Chatbot chạy bên trong 3ds Max |
| [`max_bridge_startup.ms`](file:///d:/Dropbox/_Documents/RevitAI/3dsmax/max_bridge_startup.ms) | Bộ nạp tự động MAXScript & MacroScript tạo nút bấm trên giao diện |
| [`max_cli.py`](file:///d:/Dropbox/_Documents/RevitAI/3dsmax/max_cli.py) | Công cụ dòng lệnh CLI để AI và bạn điều khiển 3ds Max từ bên ngoài |
| [`install_3dsmax_bridge.py`](file:///d:/Dropbox/_Documents/RevitAI/3dsmax/install_3dsmax_bridge.py) | Script cài đặt hook startup cho mọi phiên bản 3ds Max trên máy |
