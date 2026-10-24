using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Events;
using Autodesk.Revit.UI;
using Autodesk.Revit.UI.Events;

namespace RevitScript
{
    public class ProcessCoolermasterMep
    {
        private static string _logFile = @"D:\Dropbox\_Documents\RevitAI\mep_merge_log.txt";

        private static void Log(string msg)
        {
            try
            {
                string line = $"[{DateTime.Now:HH:mm:ss}] {msg}";
                File.AppendAllText(_logFile, line + Environment.NewLine);
            }
            catch { }
        }

        private static void OnDialogShowing(object? sender, DialogBoxShowingEventArgs e)
        {
            if (e is TaskDialogShowingEventArgs td)
            {
                Log($"[DIALOG SHOWN] ID: {td.DialogId}, Message: {td.Message}");
                td.OverrideResult((int)TaskDialogResult.Ok);
            }
            else
            {
                Log($"[NATIVE DIALOG] ID: {e.DialogId}");
            }
        }

        private static void OnFailures(object? sender, FailuresProcessingEventArgs e)
        {
            var fa = e.GetFailuresAccessor();
            var msgs = fa.GetFailureMessages();
            if (msgs == null || msgs.Count == 0) return;

            bool hasErrors = false;
            foreach (var m in msgs)
            {
                var sev = m.GetSeverity();
                string desc = m.GetDescriptionText();
                Log($"[FAILURE] Severity: {sev}, Text: {desc}");

                if (sev == FailureSeverity.Warning)
                {
                    fa.DeleteWarning(m);
                }
                else if (sev == FailureSeverity.Error)
                {
                    hasErrors = true;
                    bool resolved = false;

                    try
                    {
                        fa.ResolveFailure(m);
                        resolved = true;
                        Log($"[RESOLVED BY RESOLUTION] {desc}");
                    }
                    catch { }

                    if (!resolved)
                    {
                        try
                        {
                            var failingIds = m.GetFailingElementIds();
                            if (failingIds != null && failingIds.Count > 0)
                            {
                                fa.DeleteElements(failingIds.ToList());
                                resolved = true;
                                Log($"[RESOLVED BY DELETING ELEMENTS] Count: {failingIds.Count}");
                            }
                        }
                        catch (Exception exDel)
                        {
                            Log($"[DELETE FAIL] {exDel.Message}");
                        }
                    }
                }
            }

            if (hasErrors)
            {
                e.SetProcessingResult(FailureProcessingResult.ProceedWithCommit);
            }
            else
            {
                e.SetProcessingResult(FailureProcessingResult.Continue);
            }
        }

        public static object Run(UIApplication uiapp, dynamic args)
        {
            File.WriteAllText(_logFile, $"=== BẮT ĐẦU XỬ LÝ MEP & BUSWAY MODEL ===\n");
            var uidoc = uiapp.ActiveUIDocument;
            var hostDoc = uidoc?.Document;
            if (hostDoc == null)
            {
                string hostPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Documents\[fixed]Clooler Master Phase 2 - Nha Xuong - FFS - Branch_detached_phannguyenbuu@gmail.com.rvt";
                Log($"[MỞ FILE CHỦ] Đang mở tài liệu chủ: {hostPath}...");
                try
                {
                    uidoc = uiapp.OpenAndActivateDocument(hostPath);
                    hostDoc = uidoc?.Document;
                    Log($"[MỞ FILE CHỦ THÀNH CÔNG] Tiêu đề: {hostDoc?.Title}");
                }
                catch (Exception exHost)
                {
                    Log($"[LỖI MỞ FILE CHỦ] {exHost.Message}");
                    return new { success = false, error = "Không thể mở file chủ: " + exHost.Message };
                }
            }

            string baseDir = @"D:\Dropbox\_Documents\_KIEN TRUC 2026\CM Fire Protect\Coolermaster 2 - BIM model";

            var filesToProcess = new[]
            {
                new
                {
                    OriginalName = "CMF 2 - CO - Nha Xuong.rvt",
                    UpgradedName = "CMF 2 - CO - Nha Xuong_2025.rvt",
                    IsWorkshared = true
                },
                new
                {
                    OriginalName = "CMF 2 - ELECTRIC STATION ( bổ sung 12 tuyến busway sang 3 mpđ mới).rvt",
                    UpgradedName = "CMF 2 - ELECTRIC STATION_2025.rvt",
                    IsWorkshared = false
                }
            };

            var app = uiapp.Application;
            var results = new List<object>();

            // Đăng ký event bắt dialog tự động
            uiapp.DialogBoxShowing += OnDialogShowing;
            app.FailuresProcessing += OnFailures;

            try
            {
                foreach (var item in filesToProcess)
                {
                    string origPath = Path.Combine(baseDir, item.OriginalName);
                    string upgrPath = Path.Combine(baseDir, item.UpgradedName);

                    Log($"\n--- Bắt đầu xử lý: {item.OriginalName} ---");

                    if (!File.Exists(origPath))
                    {
                        Log($"[LỖI] Không tìm thấy file: {origPath}");
                        results.Add(new { file = item.OriginalName, status = "NotFound" });
                        continue;
                    }

                    // Bước 1: Nâng cấp và lưu sang file _2025.rvt (nếu chưa có hoặc tạo mới)
                    bool upgradeSuccess = false;
                    if (File.Exists(upgrPath) && new FileInfo(upgrPath).Length > 1024 * 1024)
                    {
                        Log($"[ĐÃ CÓ SẴN] File 2025 đã tồn tại: {item.UpgradedName} ({new FileInfo(upgrPath).Length / 1024 / 1024} MB). Dùng file này để link.");
                        upgradeSuccess = true;
                    }
                    else
                    {
                        Log($"[MỞ NÂNG CẤP] Đang mở {item.OriginalName} (Audit=false, Detach={item.IsWorkshared})...");
                        Document? openedDoc = null;
                        try
                        {
                            var openOpts = new OpenOptions
                            {
                                Audit = false
                            };
                            if (item.IsWorkshared)
                            {
                                openOpts.DetachFromCentralOption = DetachFromCentralOption.DetachAndPreserveWorksets;
                            }

                            var mPath = ModelPathUtils.ConvertUserVisiblePathToModelPath(origPath);
                            openedDoc = app.OpenDocumentFile(mPath, openOpts);

                            Log($"[MỞ THÀNH CÔNG] Tiêu đề: {openedDoc.Title}. Đang lưu sang {item.UpgradedName}...");

                            var saveOpts = new SaveAsOptions
                            {
                                OverwriteExistingFile = true,
                                Compact = true
                            };
                            if (item.IsWorkshared)
                            {
                                var wsOpts = new WorksharingSaveAsOptions
                                {
                                    SaveAsCentral = true
                                };
                                saveOpts.SetWorksharingOptions(wsOpts);
                            }

                            var upgrModelPath = ModelPathUtils.ConvertUserVisiblePathToModelPath(upgrPath);
                            openedDoc.SaveAs(upgrModelPath, saveOpts);
                            Log($"[LƯU THÀNH CÔNG] Đã lưu xong file 2025: {upgrPath}");
                            upgradeSuccess = true;
                        }
                        catch (Exception exOpen)
                        {
                            Log($"[LỖI NÂNG CẤP/LƯU] {exOpen.Message}");
                        }
                        finally
                        {
                            if (openedDoc != null)
                            {
                                try { openedDoc.Close(false); Log("[ĐÃ ĐÓNG] Đã đóng tài liệu nâng cấp."); } catch { }
                            }
                        }
                    }

                    // Bước 2: Liên kết vào tài liệu chủ hostDoc
                    if (upgradeSuccess)
                    {
                        Log($"[LIÊN KẾT] Đang nạp link vào file tổng: {item.UpgradedName}...");
                        try
                        {
                            var linkPathToUse = File.Exists(upgrPath) ? upgrPath : origPath;
                            var linkModelPath = ModelPathUtils.ConvertUserVisiblePathToModelPath(linkPathToUse);

                            using (var t = new Transaction(hostDoc, "Link " + item.OriginalName))
                            {
                                var failOpts = t.GetFailureHandlingOptions();
                                failOpts.SetFailuresPreprocessor(new LinkWarningSwallower());
                                t.SetFailureHandlingOptions(failOpts);

                                t.Start();

                                // Kiểm tra xem link type đã tồn tại chưa
                                var existingLink = new FilteredElementCollector(hostDoc)
                                    .OfClass(typeof(RevitLinkType))
                                    .Cast<RevitLinkType>()
                                    .FirstOrDefault(lt => (lt.Name ?? "").Contains(Path.GetFileNameWithoutExtension(item.OriginalName), StringComparison.OrdinalIgnoreCase)
                                                       || (lt.Name ?? "").Contains(Path.GetFileNameWithoutExtension(item.UpgradedName), StringComparison.OrdinalIgnoreCase));

                                if (existingLink != null)
                                {
                                    Log($"[RELOAD LINK] Tìm thấy RevitLinkType ID: {existingLink.Id.Value}. Đang reload...");
                                    var reloadRes = existingLink.LoadFrom(linkModelPath, null);
                                    Log($"[RELOAD KẾT QUẢ] {reloadRes.LoadResult}");

                                    var inst = new FilteredElementCollector(hostDoc)
                                        .OfClass(typeof(RevitLinkInstance))
                                        .Cast<RevitLinkInstance>()
                                        .FirstOrDefault(i => i.GetTypeId() == existingLink.Id);

                                    if (inst == null)
                                    {
                                        var newInst = RevitLinkInstance.Create(hostDoc, existingLink.Id);
                                        Log($"[TẠO INSTANCE MỚI] ID: {newInst.Id.Value}");
                                    }
                                    else
                                    {
                                        Log($"[INSTANCE ĐÃ CÓ] ID: {inst.Id.Value}");
                                    }

                                    results.Add(new { file = item.OriginalName, action = "Reloaded", status = reloadRes.LoadResult.ToString() });
                                }
                                else
                                {
                                    var linkOpts = new RevitLinkOptions(false);
                                    var createRes = RevitLinkType.Create(hostDoc, linkModelPath, linkOpts);
                                    if (createRes.ElementId != ElementId.InvalidElementId)
                                    {
                                        var newInst = RevitLinkInstance.Create(hostDoc, createRes.ElementId);
                                        Log($"[LINK THÀNH CÔNG] TypeId: {createRes.ElementId.Value}, InstanceId: {newInst.Id.Value}, Status: {createRes.LoadResult}");
                                        results.Add(new { file = item.OriginalName, action = "Created", typeId = createRes.ElementId.Value, instId = newInst.Id.Value, status = createRes.LoadResult.ToString() });
                                    }
                                    else
                                    {
                                        Log($"[LINK THẤT BẠI] Status: {createRes.LoadResult}");
                                        results.Add(new { file = item.OriginalName, action = "Failed", status = createRes.LoadResult.ToString() });
                                    }
                                }

                                t.Commit();
                                Log($"[TRANSACTION COMMIT] Hoàn tất liên kết {item.OriginalName}!");
                            }
                        }
                        catch (Exception exLink)
                        {
                            Log($"[LỖI LIÊN KẾT] {exLink.Message}");
                            results.Add(new { file = item.OriginalName, action = "Exception", error = exLink.Message });
                        }
                    }
                }
            }
            finally
            {
                uiapp.DialogBoxShowing -= OnDialogShowing;
                app.FailuresProcessing -= OnFailures;
                Log("=== HOÀN TẤT TOÀN BỘ QUÁ TRÌNH ===");
            }

            return new { success = true, results, log = File.ReadAllText(_logFile) };
        }
    }
}
