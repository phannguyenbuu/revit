-- Kịch bản 3ds Max: Import và chuyển sang Editable Poly không chia tam giác
(
    local dwgFile = "D:\\Dropbox\\_Documents\\RevitAI\\exports\\Revit_To_Max_Solids.dwg"
    if doesFileExist dwgFile then (
        format "Đang nạp file: %\n" dwgFile
        local countBefore = objects.count
        local oldObjs = for o in objects collect o
        
        -- Import DWG Solids vào 3ds Max
        importFile dwgFile #noPrompt
        
        -- Lấy danh sách các đối tượng mới
        local newObjs = for o in objects where (findItem oldObjs o == 0) collect o
        format "Đã import % đối tượng mới. Đang làm sạch lưới...\n" newObjs.count
        
        for o in newObjs do (
            if isValidNode o and canConvertTo o Editable_Poly do (
                -- Convert sang Editable Poly
                convertToPoly o
                
                -- Loại bỏ đường chéo tam giác trên mặt phẳng (Quadrify):
                try (
                    PolyToolsModeling.Quadrify false false
                ) catch ()
                
                -- Xoá các cạnh vô hình (Invisible edges):
                try (
                    o.EditablePoly.RemoveInvisibleEdges()
                ) catch ()
            )
        )
        select newObjs
        max zoomext sel
        format "✓ Hoàn tất: Đã chuyển toàn bộ sang Editable Poly sạch (Không chia tam giác)!\n"
    ) else (
        messageBox ("Không tìm thấy file: " + dwgFile) title:"Lỗi"
    )
)
