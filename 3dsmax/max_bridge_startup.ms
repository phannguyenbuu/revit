/*
================================================================================
  3ds Max AI Copilot Bridge & Chatbot Auto-Starter
  Author: Antigravity AI
  Repository: d:\Dropbox\_Documents\RevitAI\3dsmax\
================================================================================
*/

macroScript MaxAIChatbot
category:"AI Tools"
buttonText:"AI Copilot"
toolTip:"Hiện / Ẩn AI Copilot (Dock lề phải Command Panel)"
icon:#("SubObjectIcons", 1)
(
    on execute do
    (
        local bridgeScript = @"d:\Dropbox\_Documents\RevitAI\3dsmax\max_bridge.py"
        if (doesFileExist bridgeScript) then
        (
            try
            (
                python.Execute "import sys; sys.path.insert(0, r'd:\\Dropbox\\_Documents\\RevitAI\\3dsmax'); import max_bridge; max_bridge.toggle_ui()"
                format "[MaxAI] Toggle AI Copilot Panel lề phải thành công.\n"
            )
            catch
            (
                format "[MaxAI LỖI]: Không thể toggle AI Copilot: %\n" (getCurrentException())
            )
        )
        else
        (
            messageBox ("Không tìm thấy file bridge tại:\n" + bridgeScript) title:"MaxAI Error"
        )
    )
)

macroScript ExportFBXSelection
category:"AI Tools"
buttonText:"Export FBX"
toolTip:"Xuất file FBX cho selection vào D:\Dropbox\3DLib\mesh\FBX\{maxfilename}.fbx (Tự động batch nếu chọn Rectangle)"
icon:#("SubObjectIcons", 2)
(
    on execute do
    (
        local bridgeScript = @"d:\Dropbox\_Documents\RevitAI\3dsmax\max_bridge.py"
        if (doesFileExist bridgeScript) then
        (
            try
            (
                python.Execute "import sys; sys.path.insert(0, r'd:\\Dropbox\\_Documents\\RevitAI\\3dsmax'); import max_bridge; max_bridge.run_on_main_thread(max_bridge.export_selection_to_fbx)"
            )
            catch
            (
                format "[MaxAI LỖI]: Không thể xuất FBX: %\n" (getCurrentException())
            )
        )
        else
        (
            messageBox ("Không tìm thấy file bridge tại:\n" + bridgeScript) title:"MaxAI Error"
        )
    )
)

macroScript ExportFBXByRectangles
category:"AI Tools"
buttonText:"FBX Rectangles"
toolTip:"Xuất FBX theo từng Rectangle: lọc các vật thể lọt lòng XY, đưa về gốc (0,0) -> D:\Dropbox\3DLib\mesh\FBX\{maxfilename}_{rect}.fbx"
icon:#("SubObjectIcons", 3)
(
    on execute do
    (
        local bridgeScript = @"d:\Dropbox\_Documents\RevitAI\3dsmax\max_bridge.py"
        if (doesFileExist bridgeScript) then
        (
            try
            (
                python.Execute "import sys; sys.path.insert(0, r'd:\\Dropbox\\_Documents\\RevitAI\\3dsmax'); import max_bridge; max_bridge.run_on_main_thread(max_bridge.export_rectangles_batch)"
            )
            catch
            (
                format "[MaxAI LỖI]: Không thể xuất FBX theo Rectangle: %\n" (getCurrentException())
            )
        )
        else
        (
            messageBox ("Không tìm thấy file bridge tại:\n" + bridgeScript) title:"MaxAI Error"
        )
    )
)

-- Tiện ích gắn trực tiếp vào Command Panel (Tab Utilities 🔨)
utility AICopilotUtility "AI Copilot"
(
    group "AI Copilot Studio"
    (
        label lbl_port "Bridge: Port 8096" align:#center
        button btn_export "📤 Export" width:68 height:26 across:2 tooltip:"Lệnh File -> Export gốc của 3ds Max"
        button btn_import "📥 Import" width:68 height:26 tooltip:"Lệnh File -> Import gốc của 3ds Max"
        button btn_fbx "📦 Xuất FBX Selection" width:140 height:28 tooltip:"Xuất các đối tượng đang chọn ra file FBX (Tự động batch nếu chọn Rectangle)"
        button btn_fbx_rect "📐 Xuất FBX Rectangles" width:140 height:28 tooltip:"Lọc vật thể lọt trong bbox XY từng Rectangle, đưa về (0,0) xuất FBX"
        button btn_toolbar "🛠️ Hiện Toolbar" width:140 height:24 tooltip:"Ghim thanh công cụ AI Tools lên trên cùng"
        button btn_toggle "Hiện/Ẩn Dock Lề Phải" width:140 height:26 tooltip:"Bật hoặc tắt panel AI Copilot ở lề phải"
        button btn_reload "Nạp Lại Giao Diện" width:140 height:24 tooltip:"Làm mới panel AI Copilot"
    )

    on btn_export pressed do
    (
        max file export
    )

    on btn_import pressed do
    (
        max file import
    )

    on btn_fbx pressed do
    (
        python.Execute "import sys; sys.path.insert(0, r'd:\\Dropbox\\_Documents\\RevitAI\\3dsmax'); import max_bridge; max_bridge.run_on_main_thread(max_bridge.export_selection_to_fbx)"
    )

    on btn_fbx_rect pressed do
    (
        python.Execute "import sys; sys.path.insert(0, r'd:\\Dropbox\\_Documents\\RevitAI\\3dsmax'); import max_bridge; max_bridge.run_on_main_thread(max_bridge.export_rectangles_batch)"
    )

    on btn_toolbar pressed do
    (
        python.Execute "import sys; sys.path.insert(0, r'd:\\Dropbox\\_Documents\\RevitAI\\3dsmax'); import max_bridge; max_bridge.create_ai_toolbar()"
    )

    on btn_toggle pressed do
    (
        python.Execute "import sys; sys.path.insert(0, r'd:\\Dropbox\\_Documents\\RevitAI\\3dsmax'); import max_bridge; max_bridge.toggle_ui()"
    )

    on btn_reload pressed do
    (
        python.Execute "import sys, importlib; sys.path.insert(0, r'd:\\Dropbox\\_Documents\\RevitAI\\3dsmax'); import max_bridge; importlib.reload(max_bridge); max_bridge.start_bridge_server(show_ui=True)"
    )
)

-- Tự động chạy khi khởi động 3ds Max
(
    local bridgeScript = @"d:\Dropbox\_Documents\RevitAI\3dsmax\max_bridge.py"
    if (doesFileExist bridgeScript) do
    (
        try
        (
            python.ExecuteFile bridgeScript
            format "[MaxAI] 3ds Max AI Bridge & Dock Panel đã tự động tích hợp ở lề phải.\n"
        )
        catch
        (
            format "[MaxAI] Khởi động nền bridge lỗi: %\n" (getCurrentException())
        )
    )
)
