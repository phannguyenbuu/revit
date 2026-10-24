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

| Tập tin | Chức năng |
| :--- | :--- |
| [`max_bridge.py`](file:///d:/Dropbox/_Documents/RevitAI/3dsmax/max_bridge.py) | Bridge Server (HTTP) & Giao diện PySide Chatbot chạy bên trong 3ds Max |
| [`max_bridge_startup.ms`](file:///d:/Dropbox/_Documents/RevitAI/3dsmax/max_bridge_startup.ms) | Bộ nạp tự động MAXScript & MacroScript tạo nút bấm trên giao diện |
| [`max_cli.py`](file:///d:/Dropbox/_Documents/RevitAI/3dsmax/max_cli.py) | Công cụ dòng lệnh CLI để AI và bạn điều khiển 3ds Max từ bên ngoài |
| [`install_3dsmax_bridge.py`](file:///d:/Dropbox/_Documents/RevitAI/3dsmax/install_3dsmax_bridge.py) | Script cài đặt hook startup cho mọi phiên bản 3ds Max trên máy |
