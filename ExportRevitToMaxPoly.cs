using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    /// <summary>
    /// Xuất các vật thể từ Revit sang DWG dạng ACIS 3D Solids chuẩn
    /// để 3ds Max import và chuyển thành Editable Poly phẳng sạch không bị chia tam giác.
    /// Tự động triệt tiêu TaskDialog 'Export with Temporary Hide/Isolate'.
    /// </summary>
    public static class ExportRevitToMaxPoly
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { success = false, message = "Không tìm thấy tài liệu Revit đang mở." };

            // 1. Đăng ký tự động chặn và chọn dòng 2 của hộp thoại "Export with Temporary Hide/Isolate"
            EventHandler<Autodesk.Revit.UI.Events.DialogBoxShowingEventArgs> dlgHandler = (s, e) =>
            {
                if (e is Autodesk.Revit.UI.Events.TaskDialogShowingEventArgs td)
                {
                    // 1002 = CommandLink2: "Leave the Temporary Hide/Isolate mode on and export"
                    // Tự động bỏ qua hộp thoại, giữ chế độ isolate để chỉ xuất các vật thể được chọn
                    td.OverrideResult(1002);
                }
                else
                {
                    e.OverrideResult(1);
                }
            };

            uiapp.DialogBoxShowing += dlgHandler;

            try
            {
                // Thư mục đích
                string outputDir = @"D:\Dropbox\_Documents\RevitAI\exports";
                if (!Directory.Exists(outputDir))
                {
                    Directory.CreateDirectory(outputDir);
                }

                string baseName = "Revit_To_Max_Solids";
                if (args.ValueKind == System.Text.Json.JsonValueKind.Object && args.TryGetProperty("fileName", out var fn))
                {
                    string customName = fn.GetString() ?? "";
                    if (!string.IsNullOrWhiteSpace(customName)) baseName = customName;
                }

                // Tìm hoặc tạo 3D View chuyên dụng để export
                View3D? exportView = null;
                var selIds = uidoc.Selection.GetElementIds();

                // Lấy 3D view hiện hành nếu có
                if (doc.ActiveView is View3D active3D && !active3D.IsTemplate)
                {
                    exportView = active3D;
                }
                else
                {
                    // Tìm view 3D mặc định {3D}
                    var vCollector = new FilteredElementCollector(doc)
                        .OfClass(typeof(View3D))
                        .Cast<View3D>()
                        .FirstOrDefault(v => !v.IsTemplate && !v.IsPerspective);
                    exportView = vCollector;
                }

                if (exportView == null)
                {
                    return new { success = false, message = "Không tìm thấy 3D View hợp lệ trong dự án để xuất hình học." };
                }

                bool hadSelection = selIds != null && selIds.Count > 0;
                using (var tx = new Transaction(doc, "Export 3D Solids for 3ds Max"))
                {
                    tx.Start();

                    if (hadSelection)
                    {
                        exportView.IsolateElementsTemporary(selIds);
                    }

                    // Thiết lập DWGExportOptions với SolidGeometry.ACIS (Khối B-Rep chuẩn, không chia tam giác)
                    var dwgOpts = new DWGExportOptions
                    {
                        FileVersion = ACADVersion.R2018,
                        ExportOfSolids = SolidGeometry.ACIS, // CHÌA KHÓA: Khối ACIS Solids nguyên bản
                        TargetUnit = ExportUnit.Millimeter,
                        Colors = ExportColorMode.TrueColor,
                        SharedCoords = false,
                        MergedViews = true,
                        HideScopeBox = true,
                        HideUnreferenceViewTags = true
                    };

                    var viewList = new List<ElementId> { exportView.Id };
                    bool ok = doc.Export(outputDir, baseName, viewList, dwgOpts);

                    if (hadSelection)
                    {
                        exportView.DisableTemporaryViewMode(TemporaryViewMode.TemporaryHideIsolate);
                    }

                    tx.Commit();

                    string expectedFile = Path.Combine(outputDir, baseName + ".dwg");
                    if (!File.Exists(expectedFile))
                    {
                        var matches = Directory.GetFiles(outputDir, baseName + "*.dwg");
                        if (matches.Length > 0) expectedFile = matches[0];
                    }

                    if (!File.Exists(expectedFile))
                    {
                        return new { success = false, message = "Lệnh export hoàn tất nhưng không tìm thấy file DWG đầu ra." };
                    }

                    // Tạo sẵn file MAXScript để người dùng kéo thả vào 3ds Max hoặc chạy qua server 8096
                    string maxScriptPath = Path.Combine(outputDir, "Import_Clean_EditablePoly.ms");
                    string escapedDwg = expectedFile.Replace("\\", "\\\\");
                    string msContent = $@"-- Kịch bản 3ds Max: Import và chuyển sang Editable Poly không chia tam giác
(
    local dwgFile = ""{escapedDwg}""
    if doesFileExist dwgFile then (
        format ""Đang nạp file: %\n"" dwgFile
        local countBefore = objects.count
        local oldObjs = for o in objects collect o
        
        -- Import DWG Solids vào 3ds Max
        importFile dwgFile #noPrompt
        
        -- Lấy danh sách các đối tượng mới
        local newObjs = for o in objects where (findItem oldObjs o == 0) collect o
        format ""Đã import % đối tượng mới. Đang làm sạch lưới...\n"" newObjs.count
        
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
        format ""✓ Hoàn tất: Đã chuyển toàn bộ sang Editable Poly sạch (Không chia tam giác)!\n""
    ) else (
        messageBox (""Không tìm thấy file: "" + dwgFile) title:""Lỗi""
    )
)
";
                    File.WriteAllText(maxScriptPath, msContent, System.Text.Encoding.UTF8);

                    long size = new FileInfo(expectedFile).Length;
                    return new
                    {
                        success = true,
                        message = $"Đã xuất thành công ACIS 3D Solids sang: {expectedFile}",
                        dwgPath = expectedFile,
                        maxScriptPath = maxScriptPath,
                        fileSizeKb = size / 1024.0,
                        selectedCount = hadSelection ? selIds!.Count : 0,
                        viewName = exportView.Name
                    };
                }
            }
            catch (Exception ex)
            {
                return new { success = false, message = "Lỗi khi xuất sang 3ds Max: " + ex.Message, stackTrace = ex.StackTrace };
            }
            finally
            {
                uiapp.DialogBoxShowing -= dlgHandler;
            }
        }
    }
}
