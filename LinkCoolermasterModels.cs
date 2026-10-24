using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class LinkWarningSwallower : IFailuresPreprocessor
    {
        public FailureProcessingResult PreprocessFailures(FailuresAccessor failuresAccessor)
        {
            var msgs = failuresAccessor.GetFailureMessages();
            foreach (var msg in msgs)
            {
                if (msg.GetSeverity() == FailureSeverity.Warning)
                {
                    failuresAccessor.DeleteWarning(msg);
                }
            }
            return FailureProcessingResult.Continue;
        }
    }

    public class LinkCoolermasterModels
    {
        public static object Run(UIApplication uiapp, dynamic args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { success = false, error = "Không có tài liệu Revit nào đang mở!" };

            string baseDir = @"D:\Dropbox\_Documents\_KIEN TRUC 2026\CM Fire Protect\Coolermaster 2 - BIM model";

            var targetFiles = new List<string>
            {
                Path.Combine(baseDir, "CMF2_NHAXUONG_A.rvt"),
                Path.Combine(baseDir, "CMF2_NHAXUONG_S.rvt"),
                Path.Combine(baseDir, "CMF 2 - CO - Nha Xuong.rvt"),
                Path.Combine(baseDir, "CMF 2 - ELECTRIC STATION ( bổ sung 12 tuyến busway sang 3 mpđ mới).rvt")
            };

            var existingLinkTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(RevitLinkType))
                .Cast<RevitLinkType>()
                .ToList();

            var logs = new List<string>();
            var results = new List<object>();

            using (var tx = new Transaction(doc, "Ghep cac model Coolermaster"))
            {
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new LinkWarningSwallower());
                tx.SetFailureHandlingOptions(opt);

                tx.Start();

                foreach (var filePath in targetFiles)
                {
                    string fName = Path.GetFileName(filePath);
                    string nameNoExt = Path.GetFileNameWithoutExtension(filePath);

                    if (!File.Exists(filePath))
                    {
                        results.Add(new { file = fName, status = "File does not exist", path = filePath });
                        logs.Add($"[NOT FOUND] {fName}");
                        continue;
                    }

                    // Tìm xem đã có RevitLinkType nào tương tự chưa
                    var matchType = existingLinkTypes.FirstOrDefault(lt =>
                    {
                        string ltName = lt.Name ?? "";
                        return ltName.Contains(nameNoExt, StringComparison.OrdinalIgnoreCase)
                            || ltName.Contains(fName, StringComparison.OrdinalIgnoreCase)
                            || nameNoExt.Contains(ltName, StringComparison.OrdinalIgnoreCase);
                    });

                    ModelPath modelPath = ModelPathUtils.ConvertUserVisiblePathToModelPath(filePath);

                    if (matchType != null)
                    {
                        // Đã có RevitLinkType -> Cập nhật đường dẫn và Reload
                        try
                        {
                            var loadResult = matchType.LoadFrom(modelPath, null);
                            logs.Add($"[RELOADED] {fName} (TypeId: {matchType.Id.Value}, Status: {loadResult.LoadResult})");

                            // Đảm bảo có Instance trên màn hình
                            var existingInsts = new FilteredElementCollector(doc)
                                .OfClass(typeof(RevitLinkInstance))
                                .Cast<RevitLinkInstance>()
                                .Where(inst => inst.GetTypeId() == matchType.Id)
                                .ToList();

                            long instId = -1;
                            if (existingInsts.Count == 0)
                            {
                                var newInst = RevitLinkInstance.Create(doc, matchType.Id);
                                instId = newInst.Id.Value;
                                logs.Add($"  -> Tạo mới RevitLinkInstance ID: {instId}");
                            }
                            else
                            {
                                instId = existingInsts.First().Id.Value;
                                logs.Add($"  -> Đã có RevitLinkInstance ID: {instId}");
                            }

                            results.Add(new
                            {
                                file = fName,
                                action = "Reloaded",
                                linkTypeId = matchType.Id.Value,
                                instanceId = instId,
                                loadResult = loadResult.LoadResult.ToString()
                            });
                        }
                        catch (Exception ex)
                        {
                            logs.Add($"[ERROR RELOADING] {fName}: {ex.Message}");
                            results.Add(new { file = fName, action = "ReloadFailed", error = ex.Message });
                        }
                    }
                    else
                    {
                        // Chưa có -> Tạo mới RevitLinkType và RevitLinkInstance
                        try
                        {
                            var linkOpts = new RevitLinkOptions(false);
                            var linkResult = RevitLinkType.Create(doc, modelPath, linkOpts);

                            if (linkResult.ElementId != ElementId.InvalidElementId)
                            {
                                var newInst = RevitLinkInstance.Create(doc, linkResult.ElementId);
                                logs.Add($"[CREATED & LINKED] {fName} (TypeId: {linkResult.ElementId.Value}, InstId: {newInst.Id.Value})");
                                results.Add(new
                                {
                                    file = fName,
                                    action = "Created",
                                    linkTypeId = linkResult.ElementId.Value,
                                    instanceId = newInst.Id.Value,
                                    loadResult = linkResult.LoadResult.ToString()
                                });
                            }
                            else
                            {
                                logs.Add($"[FAILED CREATE LINK] {fName} - LoadResult: {linkResult.LoadResult}");
                                results.Add(new { file = fName, action = "CreateFailed", loadResult = linkResult.LoadResult.ToString() });
                            }
                        }
                        catch (Exception ex)
                        {
                            logs.Add($"[ERROR CREATING] {fName}: {ex.Message}");
                            results.Add(new { file = fName, action = "CreateException", error = ex.Message });
                        }
                    }
                }

                tx.Commit();
            }

            return new
            {
                success = true,
                docTitle = doc.Title,
                results,
                logs
            };
        }
    }
}
