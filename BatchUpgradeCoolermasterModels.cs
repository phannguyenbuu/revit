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
    public class BatchUpgradeCoolermasterModels
    {
        private static string _logFile = @"D:\Dropbox\_Documents\RevitAI\mep_upgrade_batch_log.txt";

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
                e.OverrideResult(1); // IDOK
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
                    try
                    {
                        fa.ResolveFailure(m);
                        Log($"[RESOLVED] {desc}");
                    }
                    catch { }
                }
            }

            if (hasErrors)
                e.SetProcessingResult(FailureProcessingResult.ProceedWithCommit);
            else
                e.SetProcessingResult(FailureProcessingResult.Continue);
        }

        public static object Run(UIApplication uiapp, dynamic args)
        {
            File.WriteAllText(_logFile, $"=== BẮT ĐẦU NÂNG CẤP VÀ LƯU CỐ ĐỊNH REVIT 2025 HÀNG LOẠT ===\n");
            var app = uiapp.Application;
            var uidoc = uiapp.ActiveUIDocument;
            var hostDoc = uidoc?.Document;

            string baseDir = @"D:\Dropbox\_Documents\_KIEN TRUC 2026\CM Fire Protect\Coolermaster 2 - BIM model";

            // Danh sách các file cần nâng cấp vĩnh viễn
            var targetFiles = new List<string>
            {
                "CMF2_NHAXUONG_A.rvt",
                "CMF2_NHAXUONG_S.rvt",
                "CMF2_NHAPHUTRO_A.rvt",
                "CMF2_NHAPHUTRO_S.rvt"
            };

            var results = new List<object>();

            // Đăng ký event bắt dialog
            uiapp.DialogBoxShowing += OnDialogShowing;
            app.FailuresProcessing += OnFailures;

            try
            {
                // Tìm các link trong hostDoc nếu có
                var linkTypes = hostDoc != null
                    ? new FilteredElementCollector(hostDoc).OfClass(typeof(RevitLinkType)).Cast<RevitLinkType>().ToList()
                    : new List<RevitLinkType>();

                foreach (var fileName in targetFiles)
                {
                    string filePath = Path.Combine(baseDir, fileName);
                    Log($"\n>>> Xử lý file: {fileName} <<<");

                    if (!File.Exists(filePath))
                    {
                        Log($"[LỖI] Không tìm thấy file: {filePath}");
                        results.Add(new { file = fileName, status = "NotFound" });
                        continue;
                    }

                    // Tìm link tương ứng trong hostDoc
                    RevitLinkType? matchedLinkType = linkTypes.FirstOrDefault(lt =>
                        (lt.Name ?? "").Contains(Path.GetFileNameWithoutExtension(fileName), StringComparison.OrdinalIgnoreCase));

                    // 1. Tạm thời Unload link trong hostDoc để giải phóng file lock
                    if (matchedLinkType != null && hostDoc != null)
                    {
                        try
                        {
                            if (RevitLinkType.IsLoaded(hostDoc, matchedLinkType.Id))
                            {
                                Log($"[UNLOAD LINK] Đang Unload {fileName} khỏi host document để mở và ghi đè...");
                                matchedLinkType.Unload(null);
                            }
                        }
                        catch (Exception exUnload)
                        {
                            Log($"[WARN UNLOAD] {exUnload.Message}");
                        }
                    }

                    // 2. Tạo bản sao lưu dự phòng .bak_2024 nếu chưa có
                    string backupPath = filePath + ".bak_2024";
                    if (!File.Exists(backupPath))
                    {
                        try
                        {
                            File.Copy(filePath, backupPath, false);
                            Log($"[BACKUP] Đã sao lưu bản gốc 2024: {fileName}.bak_2024");
                        }
                        catch (Exception exBak)
                        {
                            Log($"[WARN BACKUP] {exBak.Message}");
                        }
                    }

                    // 3. Mở file trong Revit 2025
                    Document? docToUpgrade = null;
                    bool upgraded = false;
                    try
                    {
                        var bfi = BasicFileInfo.Extract(filePath);
                        bool isWs = bfi.IsWorkshared;
                        Log($"[INFO] Format version: {bfi.Format}, Workshared: {isWs}");

                        var openOpts = new OpenOptions { Audit = false };
                        if (isWs)
                        {
                            openOpts.DetachFromCentralOption = DetachFromCentralOption.DetachAndPreserveWorksets;
                        }

                        var mPath = ModelPathUtils.ConvertUserVisiblePathToModelPath(filePath);
                        Log($"[OPEN] Đang mở {fileName} (Revit đang nâng cấp sang 2025)...");
                        docToUpgrade = app.OpenDocumentFile(mPath, openOpts);
                        Log($"[OPEN OK] Đã mở thành công: {docToUpgrade.Title}");

                        // 4. Lưu cố định sang định dạng Revit 2025
                        var saveOpts = new SaveAsOptions
                        {
                            OverwriteExistingFile = true,
                            Compact = true
                        };
                        if (isWs)
                        {
                            saveOpts.SetWorksharingOptions(new WorksharingSaveAsOptions { SaveAsCentral = true });
                        }

                        Log($"[SAVE] Đang lưu đè file sang Revit 2025: {filePath}...");
                        docToUpgrade.SaveAs(mPath, saveOpts);
                        Log($"[SAVE OK] ĐÃ LƯU CỐ ĐỊNH THÀNH CÔNG: {fileName} (Revit 2025 Native)!");
                        upgraded = true;
                    }
                    catch (Exception exOpenSave)
                    {
                        Log($"[LỖI NÂNG CẤP/LƯU] {fileName}: {exOpenSave.Message}");
                        results.Add(new { file = fileName, status = "Error", error = exOpenSave.Message });
                    }
                    finally
                    {
                        if (docToUpgrade != null)
                        {
                            try
                            {
                                docToUpgrade.Close(false);
                                Log($"[CLOSE] Đã đóng file {fileName}.");
                            }
                            catch { }
                        }
                    }

                    // 5. Nạp lại Link vào hostDoc
                    if (upgraded && matchedLinkType != null && hostDoc != null)
                    {
                        try
                        {
                            Log($"[RELOAD LINK] Đang nạp lại {fileName} vào file tổng...");
                            var mPath = ModelPathUtils.ConvertUserVisiblePathToModelPath(filePath);
                            var reloadRes = matchedLinkType.LoadFrom(mPath, null);
                            Log($"[RELOAD RESULT] {reloadRes.LoadResult}");
                            results.Add(new { file = fileName, status = "UpgradedAndReloaded", result = reloadRes.LoadResult.ToString() });
                        }
                        catch (Exception exReload)
                        {
                            Log($"[WARN RELOAD] {exReload.Message}");
                            results.Add(new { file = fileName, status = "Upgraded", reloadError = exReload.Message });
                        }
                    }
                    else if (upgraded)
                    {
                        results.Add(new { file = fileName, status = "UpgradedSuccessfully" });
                    }
                }

                // 6. Lưu file tổng để ghi nhận toàn bộ link mới
                if (hostDoc != null)
                {
                    try
                    {
                        Log($"\n[LƯU FILE TỔNG] Đang lưu file tổng hợp để cố định toàn bộ link...");
                        hostDoc.Save();
                        Log($"[LƯU FILE TỔNG OK] Đã lưu file tổng thành công!");
                    }
                    catch (Exception exSaveHost)
                    {
                        Log($"[WARN LƯU FILE TỔNG] {exSaveHost.Message}");
                    }
                }
            }
            finally
            {
                uiapp.DialogBoxShowing -= OnDialogShowing;
                app.FailuresProcessing -= OnFailures;
                Log("\n=== HOÀN TẤT NÂNG CẤP VÀ LƯU CỐ ĐỊNH ===");
            }

            return new
            {
                success = true,
                message = "Đã hoàn tất nâng cấp và lưu cố định toàn bộ các file link sang Revit 2025!",
                results,
                log = File.ReadAllText(_logFile)
            };
        }
    }
}
