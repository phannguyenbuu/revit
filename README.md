# RevitAI: AI Copilot & MCP Bridge for Autodesk Revit (2025 / 2027)

Cầu nối giao tiếp hai chiều giữa AI (Gemini / Antigravity / MCP Clients) và Autodesk Revit 2025 / 2027 trên nền tảng .NET 10.
Tích hợp sẵn **AI Chatbot Sidebar (Dockable Pane)** ngay trong giao diện làm việc của Revit (tương tự Autodesk Assistant trên Revit 2027).

---

## 1. Cấu trúc dự án

```text
D:\Dropbox\_Documents\RevitAI\
├── RevitMcpBridge.csproj       # Project C# .NET 10 (Revit 2025 / 2027 API)
├── App.cs                      # IExternalApplication (Ribbon UI, Dockable Pane, dynamic port)
├── ChatbotPaneView.xaml        # Giao diện WPF của AI Chatbot Sidebar
├── ChatbotPaneView.xaml.cs     # Logic tương tác, xử lý prompt tự nhiên & tác vụ nhanh
├── ChatbotPaneProvider.cs      # IDockablePaneProvider đăng ký thanh bên với Revit
├── RevitBridgeHandler.cs       # IExternalEventHandler (Thread-safe Main UI Thread Queue)
├── RevitCommandDispatcher.cs   # Thư viện xử lý logic BIM & Dynamic C# runner
├── DynamicConverter.cs         # Xử lý Family RFA, Dynamic Script Runner & Inspect
├── ColorChanger.cs             # Áp dụng bộ màu chuẩn từ bản vẽ PDF (FK2025)
├── HttpServer.cs               # Async Local HTTP Server (Auto fallback port 8090 / 8088)
├── RevitMcpBridge.addin        # Manifest đăng ký Add-in với Revit
├── revit_cli.py                # Tool CLI Python điều khiển Revit qua Terminal / Prompt
├── .gitignore                  # Bỏ qua bin, obj, user files
└── README.md
```

---

## 2. Tính năng AI Chatbot Sidebar (Tương tự Revit 2027)

Khi mở Revit 2025:
- Trên thanh Ribbon chọn tab **AI Copilot** > click nút **AI Chatbot (Sidebar)**.
- Cửa sổ Chatbot dạng thanh neo (Dockable Pane) sẽ xuất hiện cố định bên phải màn hình (cạnh bảng Properties / Project Browser).
- Hỗ trợ các nút tác vụ 1 chạm:
  - 🎨 **Đổi màu FK2025**: Tự động áp dụng bộ màu chuẩn bản vẽ kỹ thuật FK2025 (Lidl Blue, Red, Yellow, White) cho các chi tiết Solid.
  - 🔍 **Soát Family**: Quét và liệt kê thể tích khối hình học, danh sách vật liệu (Materials) của Family đang mở.
  - 📊 **Thống kê**: Thống kê số lượng Level, Grid, Sheets của dự án.
  - 💾 **Lưu file**: Lưu tài liệu đang mở an toàn.
- Khung chat thông minh: Gõ trực tiếp yêu cầu bằng tiếng Việt (ví dụ: *"đổi màu các đối tượng"*, *"kiểm tra family"*, *"thống kê mô hình"*, v.v.).

---

## 3. Cách biên dịch và cài đặt

### Bước 1: Biên dịch mã nguồn
```powershell
cd "D:\Dropbox\_Documents\RevitAI"
dotnet build RevitMcpBridge.csproj -c Release
```
*(Mặc định biên dịch với Revit 2025. Để build cho 2027: `dotnet build RevitMcpBridge.csproj -c Release -p:RevitVersion=2027`)*

### Bước 2: Cài đặt vào Revit (2025 hoặc 2027)
**Cho Revit 2025:**
```powershell
$target = "$env:APPDATA\Autodesk\Revit\Addins\2025\RevitMcpBridge"
New-Item -ItemType Directory -Path $target -Force
Copy-Item ".\bin\Release\net10.0-windows\*" -Destination $target -Recurse -Force
Copy-Item ".\RevitMcpBridge.addin" "$env:APPDATA\Autodesk\Revit\Addins\2025\" -Force
```

**Cho Revit 2027:**
```powershell
$target = "$env:APPDATA\Autodesk\Revit\Addins\2027\RevitMcpBridge"
New-Item -ItemType Directory -Path $target -Force
Copy-Item ".\bin\Release\net10.0-windows\*" -Destination $target -Recurse -Force
Copy-Item ".\RevitMcpBridge.addin" "$env:APPDATA\Autodesk\Revit\Addins\2027\" -Force
```

---

## 4. Cổng giao tiếp API (Port 8090 / 8088)

Server tự động chọn port trống (Port 8090 nếu Revit 2025 CEF chiếm 8088, hoặc Port 8088 cho Revit 2027). File `bridge_port.txt` được lưu tự động để CLI tự kết nối.

| Endpoint | Method | Chức năng |
| :--- | :--- | :--- |
| `/api/status` | GET | Kiểm tra trạng thái server và lấy thông tin dự án đang mở |
| `/api/model` | GET | Lấy danh sách Level, Grid, Sheets và thống kê đối tượng |
| `/api/execute` | POST | Thực thi lệnh tạo đối tượng, đổi màu, lưu file, dynamic runner |
| `/mcp` | POST | Chuẩn Model Context Protocol (MCP JSON-RPC 2.0) |

---

## 5. Sử dụng qua Python CLI

```bash
# Kiểm tra kết nối
python revit_cli.py status

# Lấy thông tin chi tiết mô hình
python revit_cli.py model

# Kiểm tra chi tiết các đối tượng và vật liệu trong Family đang mở
python revit_cli.py inspect-family

# Đổi màu các đối tượng trong Family theo chuẩn FK2025 (Lidl Blue, Red, Yellow, White)
python revit_cli.py apply-colors

# Lưu tài liệu Revit đang mở
python revit_cli.py save
```
