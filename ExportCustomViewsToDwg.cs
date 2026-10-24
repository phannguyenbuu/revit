using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportCustomViewsToDwg
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { success = false, error = "Không có tài liệu Revit nào đang mở!" };

            var targetArgs = args.ValueKind == JsonValueKind.Object && args.TryGetProperty("args", out var innerArgs) && innerArgs.ValueKind == JsonValueKind.Object ? innerArgs : args;

            // 1. Đọc danh sách viewIds được chọn
            var viewIds = new List<long>();
            if (targetArgs.TryGetProperty("viewIds", out var pViewIds) && pViewIds.ValueKind == JsonValueKind.Array)
            {
                for (int i = 0; i < pViewIds.GetArrayLength(); i++)
                {
                    viewIds.Add(pViewIds[i].GetInt64());
                }
            }

            // Nếu không truyền viewIds: Lấy từ Selection hiện tại của người dùng trong Revit
            if (viewIds.Count == 0)
            {
                var selIds = uidoc.Selection.GetElementIds();
                foreach (var id in selIds)
                {
                    var elem = doc.GetElement(id);
                    if (elem is View v && !v.IsTemplate)
                    {
                        viewIds.Add(id.Value);
                    }
                }
            }

            // Nếu vẫn không có: Fallback 7 mặt bằng chuẩn
            if (viewIds.Count == 0)
            {
                var defaultViews = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewPlan))
                    .Cast<ViewPlan>()
                    .Where(v => !v.IsTemplate && v.ViewType == ViewType.FloorPlan)
                    .OrderBy(v => v.Name)
                    .Take(7)
                    .ToList();
                foreach (var v in defaultViews) viewIds.Add(v.Id.Value);
            }

            // 2. Đọc các tùy chọn xuất
            bool overlayTitleblock = false;
            string titleblockFile = "";
            bool combineVertical = false;
            string outputFolder = Path.Combine(@"D:\Dropbox\_Documents\RevitAI\exports", "dwg");

            if (targetArgs.TryGetProperty("overlayTitleblock", out var pOverlay)) overlayTitleblock = pOverlay.GetBoolean();
            if (targetArgs.TryGetProperty("titleblockFile", out var pTbFile)) titleblockFile = pTbFile.GetString() ?? "";
            if (targetArgs.TryGetProperty("combineVertical", out var pComb)) combineVertical = pComb.GetBoolean();
            if (targetArgs.TryGetProperty("outputFolder", out var pOut))
            {
                string customOut = pOut.GetString() ?? "";
                if (!string.IsNullOrEmpty(customOut)) outputFolder = customOut;
            }

            if (!Directory.Exists(outputFolder))
            {
                Directory.CreateDirectory(outputFolder);
            }

            // 3. Cập nhật thông tin Project Information nếu có
            if (targetArgs.TryGetProperty("projectInfo", out var pInfo) && pInfo.ValueKind == JsonValueKind.Object)
            {
                try
                {
                    using (var txPi = new Transaction(doc, "Cập nhật Thông tin Dự án khi Xuất"))
                    {
                        txPi.Start();
                        var pi = doc.ProjectInformation;
                        if (pi != null)
                        {
                            if (pInfo.TryGetProperty("projectName", out var pName) && pName.GetString() != null)
                                pi.get_Parameter(BuiltInParameter.PROJECT_NAME)?.Set(pName.GetString());
                            if (pInfo.TryGetProperty("buildingName", out var pBld) && pBld.GetString() != null)
                            {
                                try { pi.BuildingName = pBld.GetString(); } catch { pi.LookupParameter("Building Name")?.Set(pBld.GetString()); }
                            }
                            if (pInfo.TryGetProperty("projectAddress", out var pAddr) && pAddr.GetString() != null)
                                pi.get_Parameter(BuiltInParameter.PROJECT_ADDRESS)?.Set(pAddr.GetString());
                            if (pInfo.TryGetProperty("clientName", out var pClient) && pClient.GetString() != null)
                                pi.get_Parameter(BuiltInParameter.CLIENT_NAME)?.Set(pClient.GetString());
                            if (pInfo.TryGetProperty("issueDate", out var pDate) && pDate.GetString() != null)
                                pi.get_Parameter(BuiltInParameter.PROJECT_ISSUE_DATE)?.Set(pDate.GetString());
                            if (pInfo.TryGetProperty("projectNumber", out var pNum) && pNum.GetString() != null)
                                pi.get_Parameter(BuiltInParameter.PROJECT_NUMBER)?.Set(pNum.GetString());
                            if (pInfo.TryGetProperty("author", out var pAuth) && pAuth.GetString() != null)
                                pi.get_Parameter(BuiltInParameter.PROJECT_AUTHOR)?.Set(pAuth.GetString());
                        }
                        txPi.Commit();
                    }
                }
                catch {}
            }

            // 4. Thiết lập tùy chọn xuất DWG chuẩn
            var dwgOpt = new DWGExportOptions();
            dwgOpt.FileVersion = ACADVersion.R2018;
            dwgOpt.TargetUnit = ExportUnit.Millimeter;
            dwgOpt.MergedViews = true;
            dwgOpt.Colors = ExportColorMode.IndexColors; // Bảng màu chuẩn AutoCAD 256 ACI ByLayer
            dwgOpt.HideScopeBox = true;
            dwgOpt.HideUnreferenceViewTags = true;

            string filePrefix = "";
            if (targetArgs.TryGetProperty("filePrefix", out var pPrefix) && pPrefix.GetString() != null)
            {
                filePrefix = pPrefix.GetString()!.Trim();
                if (!string.IsNullOrEmpty(filePrefix)) filePrefix = filePrefix + "_";
            }

            int customOrder = 0;
            if (targetArgs.TryGetProperty("orderIndex", out var pOrder)) customOrder = pOrder.GetInt32();

            var exportedFiles = new List<object>();
            int successCount = 0;
            var exportedPaths = new List<string>();

            for (int i = 0; i < viewIds.Count; i++)
            {
                long vid = viewIds[i];
                var v = doc.GetElement(new ElementId(vid)) as View;
                if (v == null || v.IsTemplate) continue;

                // Tên file an toàn
                int currentOrder = (customOrder > 0 && viewIds.Count == 1) ? customOrder : (i + 1);
                string rawName;
                if (combineVertical)
                {
                    // Khi gộp CAD: Tên file con tạm thời bắt buộc dùng ASCII thuần không dấu và không dấu cách
                    rawName = $"view_{currentOrder:D2}";
                }
                else
                {
                    string viewPrefix = currentOrder.ToString("D2");
                    string sheetPrefix = "";
                    if (v is ViewSheet vs && !string.IsNullOrEmpty(vs.SheetNumber))
                    {
                        sheetPrefix = vs.SheetNumber + "_";
                    }
                    rawName = $"{filePrefix}{viewPrefix}_{sheetPrefix}{v.Name}".Trim();
                }
                string safeName = rawName;
                foreach (char c in Path.GetInvalidFileNameChars())
                {
                    safeName = safeName.Replace(c, '_');
                }

                // Xóa file cũ nếu tồn tại
                string targetDwg = Path.Combine(outputFolder, safeName + ".dwg");
                try
                {
                    if (File.Exists(targetDwg)) File.Delete(targetDwg);
                }
                catch {}

                bool ok = false;
                try
                {
                    ok = doc.Export(outputFolder, safeName, new List<ElementId> { v.Id }, dwgOpt);
                }
                catch (Exception ex)
                {
                    exportedFiles.Add(new
                    {
                        order = currentOrder,
                        viewId = vid,
                        viewName = v.Name,
                        isSheet = (v is ViewSheet),
                        success = false,
                        error = ex.Message
                    });
                    continue;
                }

                // Tìm file DWG vừa xuất
                string finalFile = targetDwg;
                if (!File.Exists(finalFile))
                {
                    var matches = Directory.GetFiles(outputFolder, safeName + "*.dwg");
                    if (matches.Length > 0) finalFile = matches[0];
                }

                double sizeKb = File.Exists(finalFile) ? Math.Round(new FileInfo(finalFile).Length / 1024.0, 1) : 0.0;
                if (File.Exists(finalFile))
                {
                    successCount++;
                    exportedPaths.Add(finalFile);
                }

                exportedFiles.Add(new
                {
                    order = currentOrder,
                    viewId = vid,
                    viewName = v.Name,
                    sheetNumber = (v is ViewSheet s) ? s.SheetNumber : null,
                    isSheet = (v is ViewSheet),
                    success = ok && File.Exists(finalFile),
                    filePath = File.Exists(finalFile) ? finalFile : null,
                    fileSizeKb = sizeKb
                });
            }

            return new
            {
                success = successCount > 0,
                totalRequested = viewIds.Count,
                successCount,
                outputFolder,
                overlayTitleblock,
                titleblockFile = overlayTitleblock ? titleblockFile : null,
                combineVertical,
                exportedFiles,
                exportedPaths,
                message = $"Đã xuất thành công {successCount}/{viewIds.Count} bản vẽ sang DWG tại: {outputFolder}"
            };
        }
    }
}
