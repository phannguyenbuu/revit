using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Plumbing;
using Autodesk.Revit.DB.Mechanical;
using Autodesk.Revit.DB.Electrical;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class ExportCoolermasterMepDwg
    {
        private static string _logFile = @"D:\Dropbox\_Documents\RevitAI\mep_dwg_export_log.txt";

        private static void Log(string msg)
        {
            try
            {
                string line = $"[{DateTime.Now:HH:mm:ss}] {msg}";
                File.AppendAllText(_logFile, line + Environment.NewLine);
            }
            catch { }
        }

        public class MepTradeConfig
        {
            public string Key { get; set; } = "";
            public string DisplayName { get; set; } = "";
            public string FolderName { get; set; } = "";
            public List<BuiltInCategory> VisibleCategories { get; set; } = new();
            public Func<Element, bool>? ElementFilter { get; set; }
            public Func<Element, XYZ, string>? TagFormatter { get; set; }
        }

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            File.WriteAllText(_logFile, $"=== BẮT ĐẦU XUẤT BẢN VẼ DWG MEP KÈM TAG COS CAO ĐỘ (COOLERMASTER PHASE 2) ===\n");
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null)
            {
                return new { success = false, error = "Không có tài liệu Revit nào đang mở!" };
            }

            Log($"[TÀI LIỆU CHỦ] Tiêu đề: {doc.Title}");

            // 1. Cấu hình thư mục xuất DWG
            string baseOutputDir = @"D:\Dropbox\_Documents\_KIEN TRUC 2026\CM Fire Protect\Coolermaster 2 - BIM model\DWG_MEP_Coolermaster_Phase2";
            if (args.TryGetProperty("outputDir", out var pOut) && !string.IsNullOrWhiteSpace(pOut.GetString()))
            {
                baseOutputDir = pOut.GetString()!;
            }
            Directory.CreateDirectory(baseOutputDir);

            bool tagElevation = true;
            if (args.TryGetProperty("tagElevation", out var pTag)) tagElevation = pTag.GetBoolean();

            double minLenMm = 800.0;
            if (args.TryGetProperty("minSegmentLengthMm", out var pMinLen)) minLenMm = pMinLen.GetDouble();
            double minLenFt = minLenMm / 304.8;
            double minTagSpacingFt = 3.0 / 0.3048; // Tối thiểu cách nhau 3.0m giữa các tag để bản vẽ thoáng đẹp

            // 2. Danh mục MEP tổng thể để ẩn/hiện view
            var allMepCategories = new List<BuiltInCategory>
            {
                BuiltInCategory.OST_PipeCurves,
                BuiltInCategory.OST_PipeFitting,
                BuiltInCategory.OST_PipeAccessory,
                BuiltInCategory.OST_Sprinklers,
                BuiltInCategory.OST_PlumbingFixtures,
                BuiltInCategory.OST_PlumbingEquipment,
                BuiltInCategory.OST_FlexPipeCurves,
                BuiltInCategory.OST_DuctCurves,
                BuiltInCategory.OST_DuctFitting,
                BuiltInCategory.OST_DuctAccessory,
                BuiltInCategory.OST_DuctTerminal,
                BuiltInCategory.OST_MechanicalEquipment,
                BuiltInCategory.OST_FlexDuctCurves,
                BuiltInCategory.OST_CableTray,
                BuiltInCategory.OST_CableTrayFitting,
                BuiltInCategory.OST_Conduit,
                BuiltInCategory.OST_ConduitFitting,
                BuiltInCategory.OST_ElectricalFixtures,
                BuiltInCategory.OST_ElectricalEquipment,
                BuiltInCategory.OST_LightingFixtures,
                BuiltInCategory.OST_FireAlarmDevices,
                BuiltInCategory.OST_SecurityDevices,
                BuiltInCategory.OST_CommunicationDevices
            };

            // 3. Định nghĩa các hạng mục MEP chi tiết theo yêu cầu
            var trades = new List<MepTradeConfig>
            {
                // 1. Chữa cháy (FFS / Sprinkler)
                new MepTradeConfig
                {
                    Key = "chua_chay",
                    DisplayName = "Chữa Cháy (PCCC Sprinkler)",
                    FolderName = "01_PCCC_ChuaChay",
                    VisibleCategories = new List<BuiltInCategory>
                    {
                        BuiltInCategory.OST_PipeCurves,
                        BuiltInCategory.OST_PipeFitting,
                        BuiltInCategory.OST_PipeAccessory,
                        BuiltInCategory.OST_Sprinklers,
                        BuiltInCategory.OST_PlumbingFixtures,
                        BuiltInCategory.OST_PlumbingEquipment
                    },
                    ElementFilter = elem =>
                    {
                        // Giữ ống PCCC (FFS) hoặc ống nước chữa cháy
                        string sys = elem.get_Parameter(BuiltInParameter.RBS_SYSTEM_NAME_PARAM)?.AsString() ?? "";
                        if (string.IsNullOrEmpty(sys)) return true; // Trong host doc toàn bộ là PCCC
                        return sys.Contains("FFS", StringComparison.OrdinalIgnoreCase) || sys.Contains("Fire", StringComparison.OrdinalIgnoreCase);
                    },
                    TagFormatter = (elem, mid) =>
                    {
                        if (elem is Pipe pipe)
                        {
                            double diamFt = pipe.get_Parameter(BuiltInParameter.RBS_PIPE_OUTER_DIAMETER)?.AsDouble()
                                         ?? pipe.get_Parameter(BuiltInParameter.RBS_CURVE_DIAMETER_PARAM)?.AsDouble() ?? 0;
                            double bopM = (mid.Z - diamFt / 2.0) * 0.3048;
                            string sizeStr = pipe.LookupParameter("Size")?.AsString() ?? $"DN{(int)(diamFt * 304.8)}";
                            return $"{sizeStr} • BOP {FormatElevation(bopM)}";
                        }
                        return null;
                    }
                },

                // 2. Hút khói sự cố (Smoke Exhaust)
                new MepTradeConfig
                {
                    Key = "hut_khoi",
                    DisplayName = "Hút Khói Sự Cố (Smoke Exhaust)",
                    FolderName = "02_HutKhoi_Smoke",
                    VisibleCategories = new List<BuiltInCategory>
                    {
                        BuiltInCategory.OST_DuctCurves,
                        BuiltInCategory.OST_DuctFitting,
                        BuiltInCategory.OST_DuctAccessory,
                        BuiltInCategory.OST_DuctTerminal,
                        BuiltInCategory.OST_MechanicalEquipment
                    },
                    ElementFilter = elem =>
                    {
                        string sys = elem.get_Parameter(BuiltInParameter.RBS_SYSTEM_NAME_PARAM)?.AsString() ?? "";
                        string name = elem.Name ?? "";
                        return sys.Contains("SEAD", StringComparison.OrdinalIgnoreCase)
                            || sys.Contains("Khói", StringComparison.OrdinalIgnoreCase)
                            || sys.Contains("Smoke", StringComparison.OrdinalIgnoreCase)
                            || name.Contains("Hút khói", StringComparison.OrdinalIgnoreCase)
                            || name.Contains("Smoke", StringComparison.OrdinalIgnoreCase);
                    },
                    TagFormatter = (elem, mid) =>
                    {
                        if (elem is Duct duct)
                        {
                            double hFt = duct.get_Parameter(BuiltInParameter.RBS_CURVE_HEIGHT_PARAM)?.AsDouble() ?? 0;
                            double bodM = (mid.Z - hFt / 2.0) * 0.3048;
                            string sizeStr = duct.LookupParameter("Size")?.AsString() ?? elem.Name;
                            return $"[HK] {sizeStr} • BOD {FormatElevation(bodM)}";
                        }
                        return null;
                    }
                },

                // 3. Thông gió & Bù khí (HVAC)
                new MepTradeConfig
                {
                    Key = "thong_gio",
                    DisplayName = "Thông Gió & Bù Khí (HVAC)",
                    FolderName = "03_ThongGio_HVAC",
                    VisibleCategories = new List<BuiltInCategory>
                    {
                        BuiltInCategory.OST_DuctCurves,
                        BuiltInCategory.OST_DuctFitting,
                        BuiltInCategory.OST_DuctAccessory,
                        BuiltInCategory.OST_DuctTerminal,
                        BuiltInCategory.OST_MechanicalEquipment
                    },
                    ElementFilter = elem =>
                    {
                        string sys = elem.get_Parameter(BuiltInParameter.RBS_SYSTEM_NAME_PARAM)?.AsString() ?? "";
                        // Không lấy SEAD (vì đã ở mục hút khói)
                        if (sys.Contains("SEAD", StringComparison.OrdinalIgnoreCase)) return false;
                        return true;
                    },
                    TagFormatter = (elem, mid) =>
                    {
                        if (elem is Duct duct)
                        {
                            double hFt = duct.get_Parameter(BuiltInParameter.RBS_CURVE_HEIGHT_PARAM)?.AsDouble() ?? 0;
                            double bodM = (mid.Z - hFt / 2.0) * 0.3048;
                            string sizeStr = duct.LookupParameter("Size")?.AsString() ?? elem.Name;
                            string sys = elem.get_Parameter(BuiltInParameter.RBS_SYSTEM_NAME_PARAM)?.AsString() ?? "";
                            string prefix = sys.StartsWith("BUS", StringComparison.OrdinalIgnoreCase) ? "[BUS]" :
                                            sys.StartsWith("SAD", StringComparison.OrdinalIgnoreCase) ? "[SA]" :
                                            sys.StartsWith("TED", StringComparison.OrdinalIgnoreCase) ? "[TE]" : "[TG]";
                            return $"{prefix} {sizeStr} • BOD {FormatElevation(bodM)}";
                        }
                        return null;
                    }
                },

                // 4. Điện & Máng cáp (Conduit & Cable Tray)
                new MepTradeConfig
                {
                    Key = "dien_mang_cap",
                    DisplayName = "Ống Điện & Máng Cáp (Electrical)",
                    FolderName = "04_Dien_MangCap_Conduit",
                    VisibleCategories = new List<BuiltInCategory>
                    {
                        BuiltInCategory.OST_CableTray,
                        BuiltInCategory.OST_CableTrayFitting,
                        BuiltInCategory.OST_Conduit,
                        BuiltInCategory.OST_ConduitFitting,
                        BuiltInCategory.OST_ElectricalFixtures,
                        BuiltInCategory.OST_ElectricalEquipment
                    },
                    ElementFilter = elem => true,
                    TagFormatter = (elem, mid) =>
                    {
                        if (elem is CableTray tray)
                        {
                            double hFt = tray.get_Parameter(BuiltInParameter.RBS_CABLETRAY_HEIGHT_PARAM)?.AsDouble() ?? 0;
                            double botM = (mid.Z - hFt / 2.0) * 0.3048;
                            string sizeStr = tray.LookupParameter("Size")?.AsString() ?? elem.Name;
                            return $"CT {sizeStr} • BOT {FormatElevation(botM)}";
                        }
                        if (elem is Conduit conduit)
                        {
                            double clM = mid.Z * 0.3048;
                            string sizeStr = conduit.LookupParameter("Size")?.AsString() ?? elem.Name;
                            return $"CD {sizeStr} • CL {FormatElevation(clM)}";
                        }
                        return null;
                    }
                },

                // 5. Tuyến Busway & Trạm Điện
                new MepTradeConfig
                {
                    Key = "busway",
                    DisplayName = "Tuyến Busway & Trạm Điện (Busway)",
                    FolderName = "05_Busway_TramDien",
                    VisibleCategories = new List<BuiltInCategory>
                    {
                        BuiltInCategory.OST_CableTray,
                        BuiltInCategory.OST_CableTrayFitting,
                        BuiltInCategory.OST_ElectricalEquipment,
                        BuiltInCategory.OST_GenericModel
                    },
                    ElementFilter = elem =>
                    {
                        string name = (elem.Name ?? "").ToLowerInvariant();
                        string typeName = (elem.LookupParameter("Type")?.AsString() ?? "").ToLowerInvariant();
                        return name.Contains("busway") || name.Contains("bus") || name.Contains("msb")
                            || name.Contains("tba") || name.Contains("mpđ") || name.Contains("kd3000")
                            || typeName.Contains("busway");
                    },
                    TagFormatter = (elem, mid) =>
                    {
                        double clM = mid.Z * 0.3048;
                        string label = elem.Name;
                        if (label.Length > 25) label = label.Substring(0, 25);
                        return $"[BUSWAY] {label} • CL {FormatElevation(clM)}";
                    }
                },

                // 6. Báo khói & Báo cháy (Fire Alarm)
                new MepTradeConfig
                {
                    Key = "bao_khoi",
                    DisplayName = "Báo Khói & Báo Cháy (Fire Alarm)",
                    FolderName = "06_BaoKhoi_FireAlarm",
                    VisibleCategories = new List<BuiltInCategory>
                    {
                        BuiltInCategory.OST_FireAlarmDevices,
                        BuiltInCategory.OST_SecurityDevices,
                        BuiltInCategory.OST_CommunicationDevices,
                        BuiltInCategory.OST_ElectricalEquipment,
                        BuiltInCategory.OST_Conduit,
                        BuiltInCategory.OST_ConduitFitting
                    },
                    ElementFilter = elem => true,
                    TagFormatter = (elem, mid) =>
                    {
                        double clM = mid.Z * 0.3048;
                        string label = elem.Name;
                        if (label.Length > 20) label = label.Substring(0, 20);
                        return $"[FA] {label} • {FormatElevation(clM)}";
                    }
                }
            };

            // Lọc danh sách trades nếu có chỉ định từ caller
            if (args.TryGetProperty("trades", out var pTrades) && pTrades.ValueKind == JsonValueKind.Array)
            {
                var selectedKeys = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
                for (int i = 0; i < pTrades.GetArrayLength(); i++) selectedKeys.Add(pTrades[i].GetString() ?? "");
                trades = trades.Where(t => selectedKeys.Contains(t.Key)).ToList();
            }

            // 4. Lấy danh sách các View Mặt Bằng sàn chính xác đã có sẵn trong dự án
            var existingViews = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .Where(v => !v.IsTemplate && v.ViewType == ViewType.FloorPlan && v.GenLevel != null)
                .OrderBy(v => v.GenLevel.Elevation)
                .ToList();

            // Danh sách các view mặt bằng sàn chuẩn theo tầng (bỏ trùng)
            var floorPlanViews = new List<ViewPlan>();
            var seenElevations = new HashSet<int>();
            foreach (var v in existingViews)
            {
                int elevMm = (int)Math.Round(v.GenLevel.Elevation * 304.8);
                // Bỏ qua view copy hoặc view phụ
                if (v.Name.Contains("Copy", StringComparison.OrdinalIgnoreCase) || v.Name.Contains("FFS -", StringComparison.OrdinalIgnoreCase))
                {
                    continue;
                }
                if (!seenElevations.Contains(elevMm))
                {
                    seenElevations.Add(elevMm);
                    floorPlanViews.Add(v);
                }
            }

            Log($"[DANH SÁCH MẶT BẰNG SÀN CHUẨN] Tìm thấy {floorPlanViews.Count} tầng chính:");
            foreach (var v in floorPlanViews)
            {
                Log($"  • {v.Name} (Level: {v.GenLevel.Name}, Cao độ: {v.GenLevel.Elevation * 0.3048:F3} m)");
            }

            // 5. Lấy danh sách file Revit Link đang nạp
            var linkInstances = new FilteredElementCollector(doc)
                .OfClass(typeof(RevitLinkInstance))
                .Cast<RevitLinkInstance>()
                .ToList();
            Log($"[REVIT LINKS] Tìm thấy {linkInstances.Count} link model đang kết nối.");

            // 6. Lựa chọn TextNoteType cho Tag Cos Cao Độ
            ElementId textTypeId = ElementId.InvalidElementId;
            var textTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(TextNoteType))
                .Cast<TextNoteType>()
                .ToList();
            var targetType = textTypes.FirstOrDefault(tt => tt.Name.Equals("Text Note 1", StringComparison.OrdinalIgnoreCase))
                          ?? textTypes.FirstOrDefault(tt => tt.Name.Contains("2.5") || tt.Name.Contains("Tag"))
                          ?? textTypes.FirstOrDefault();
            if (targetType != null) textTypeId = targetType.Id;

            // 7. Cấu hình DWG Export Options (AutoCAD 2018, Đơn vị mm, Màu Index ByLayer, Merged)
            var dwgOpts = new DWGExportOptions
            {
                FileVersion = ACADVersion.R2018,
                TargetUnit = ExportUnit.Millimeter,
                MergedViews = true,
                Colors = ExportColorMode.IndexColors,
                HideScopeBox = true,
                HideUnreferenceViewTags = true
            };

            var exportResults = new List<object>();
            int totalExported = 0;
            int totalTagged = 0;

            // 8. Duyệt qua từng tầng và từng hạng mục MEP để tạo View và Xuất DWG
            for (int fIdx = 0; fIdx < floorPlanViews.Count; fIdx++)
            {
                var baseView = floorPlanViews[fIdx];
                var lvl = baseView.GenLevel;
                double lvlElevFt = lvl.Elevation;
                double nextLvlElevFt = (fIdx + 1 < floorPlanViews.Count)
                    ? floorPlanViews[fIdx + 1].GenLevel.Elevation
                    : (lvlElevFt + (4.5 / 0.3048)); // default 4.5m cho tầng trên cùng

                string cleanLvlName = CleanFileName(lvl.Name);

                foreach (var trade in trades)
                {
                    string tradeSubDir = Path.Combine(baseOutputDir, trade.FolderName);
                    Directory.CreateDirectory(tradeSubDir);

                    string viewName = $"DWG_{cleanLvlName}_{trade.Key.ToUpper()}";
                    string dwgFileName = $"{cleanLvlName}_{trade.Key}";

                    Log($"\n>>> Xử lý: Tầng [{lvl.Name}] • Hạng mục [{trade.DisplayName}] <<<");

                    ViewPlan? workingView = null;
                    int taggedInView = 0;

                    using (var t = new Transaction(doc, $"Chuẩn bị View và Tag MEP {viewName}"))
                    {
                        t.Start();

                        // 1. Tạo view duplicate từ mặt bằng tầng
                        var dupId = baseView.Duplicate(ViewDuplicateOption.Duplicate);
                        workingView = doc.GetElement(dupId) as ViewPlan;
                        if (workingView == null)
                        {
                            Log($"[LỖI] Không thể duplicate view cho {viewName}");
                            t.RollBack();
                            continue;
                        }

                        try { workingView.Name = viewName; }
                        catch { workingView.Name = $"{viewName}_{DateTime.Now.Ticks % 10000}"; }

                        workingView.Scale = 100; // Tỉ lệ 1:100

                        // 2. Cô lập Category: Ẩn toàn bộ các category MEP không thuộc trade này
                        foreach (var bic in allMepCategories)
                        {
                            var cat = Category.GetCategory(doc, bic);
                            if (cat == null) continue;
                            bool isTradeCat = trade.VisibleCategories.Contains(bic);
                            if (workingView.CanCategoryBeHidden(cat.Id))
                            {
                                workingView.SetCategoryHidden(cat.Id, !isTradeCat);
                            }
                        }

                        // 3. Đặt các category Kiến trúc / Kết cấu ở chế độ Halftone làm nền mờ
                        var archBackgroundCats = new[]
                        {
                            BuiltInCategory.OST_Walls,
                            BuiltInCategory.OST_Columns,
                            BuiltInCategory.OST_StructuralColumns,
                            BuiltInCategory.OST_Floors,
                            BuiltInCategory.OST_Doors,
                            BuiltInCategory.OST_Windows,
                            BuiltInCategory.OST_Stairs
                        };
                        var halftoneOverride = new OverrideGraphicSettings();
                        halftoneOverride.SetHalftone(true);

                        foreach (var bic in archBackgroundCats)
                        {
                            var cat = Category.GetCategory(doc, bic);
                            if (cat != null && workingView.CanCategoryBeHidden(cat.Id))
                            {
                                workingView.SetCategoryHidden(cat.Id, false);
                                workingView.SetCategoryOverrides(cat.Id, halftoneOverride);
                            }
                        }

                        // 4. Lưới trục (Grids) luôn rõ nét
                        var gridCat = Category.GetCategory(doc, BuiltInCategory.OST_Grids);
                        if (gridCat != null && workingView.CanCategoryBeHidden(gridCat.Id))
                        {
                            workingView.SetCategoryHidden(gridCat.Id, false);
                        }

                        // 5. Gắn Tag Cos Cao Độ lên từng ống / máng trong phạm vi tầng
                        if (tagElevation && textTypeId != ElementId.InvalidElementId)
                        {
                            taggedInView = TagMepElementsInView(
                                doc, workingView, linkInstances, trade,
                                lvlElevFt, nextLvlElevFt, minLenFt, minTagSpacingFt, textTypeId);
                            totalTagged += taggedInView;
                        }

                        t.Commit();
                        Log($"[COMMIT VIEW] Đã chuẩn bị xong {viewName} • Đã gắn {taggedInView} tag cos cao độ.");
                    }

                    // 6. Xuất DWG bằng Revit API
                    if (workingView != null)
                    {
                        try
                        {
                            string targetDwg = Path.Combine(tradeSubDir, dwgFileName + ".dwg");
                            if (File.Exists(targetDwg)) File.Delete(targetDwg);

                            bool ok = doc.Export(tradeSubDir, dwgFileName, new List<ElementId> { workingView.Id }, dwgOpts);
                            if (ok || File.Exists(targetDwg))
                            {
                                long size = File.Exists(targetDwg) ? new FileInfo(targetDwg).Length : 0;
                                Log($"[XUẤT DWG THÀNH CÔNG] File: {dwgFileName}.dwg ({size / 1024} KB)");
                                exportResults.Add(new
                                {
                                    level = lvl.Name,
                                    trade = trade.DisplayName,
                                    fileName = dwgFileName + ".dwg",
                                    path = targetDwg,
                                    sizeBytes = size,
                                    tagsCount = taggedInView,
                                    status = "Success"
                                });
                                totalExported++;
                            }
                            else
                            {
                                Log($"[XUẤT DWG THẤT BẠI] {dwgFileName}");
                            }
                        }
                        catch (Exception exExport)
                        {
                            Log($"[LỖI XUẤT DWG] {exExport.Message}");
                        }
                    }
                }
            }

            Log($"\n=== HOÀN TẤT: Đã xuất {totalExported} file DWG • Tổng cộng {totalTagged} tag cos cao độ ===");

            return new
            {
                success = true,
                totalFiles = totalExported,
                totalTags = totalTagged,
                outputDirectory = baseOutputDir,
                files = exportResults,
                log = File.ReadAllText(_logFile)
            };
        }

        private static int TagMepElementsInView(
            Document hostDoc,
            ViewPlan view,
            List<RevitLinkInstance> links,
            MepTradeConfig trade,
            double minZFt,
            double maxZFt,
            double minLenFt,
            double minSpacingFt,
            ElementId textTypeId)
        {
            int tagCount = 0;
            var placedTagPoints = new List<XYZ>();

            // 1. Quét trong Host Document (PCCC Sprinkler)
            foreach (var cat in trade.VisibleCategories)
            {
                var elements = new FilteredElementCollector(hostDoc)
                    .OfCategory(cat)
                    .WhereElementIsNotElementType()
                    .ToList();

                foreach (var elem in elements)
                {
                    if (TagSingleElement(hostDoc, view, elem, Transform.Identity, trade, minZFt, maxZFt, minLenFt, minSpacingFt, placedTagPoints, textTypeId))
                    {
                        tagCount++;
                    }
                }
            }

            // 2. Quét trong các Link Documents (Cơ điện, Busway, Hút khói)
            foreach (var link in links)
            {
                var linkDoc = link.GetLinkDocument();
                if (linkDoc == null) continue;
                Transform tf = link.GetTotalTransform();

                foreach (var cat in trade.VisibleCategories)
                {
                    var linkElems = new FilteredElementCollector(linkDoc)
                        .OfCategory(cat)
                        .WhereElementIsNotElementType()
                        .ToList();

                    foreach (var elem in linkElems)
                    {
                        if (TagSingleElement(hostDoc, view, elem, tf, trade, minZFt, maxZFt, minLenFt, minSpacingFt, placedTagPoints, textTypeId))
                        {
                            tagCount++;
                        }
                    }
                }
            }

            return tagCount;
        }

        private static bool TagSingleElement(
            Document hostDoc,
            ViewPlan view,
            Element elem,
            Transform tf,
            MepTradeConfig trade,
            double minZFt,
            double maxZFt,
            double minLenFt,
            double minSpacingFt,
            List<XYZ> placedTagPoints,
            ElementId textTypeId)
        {
            try
            {
                if (trade.ElementFilter != null && !trade.ElementFilter(elem))
                {
                    return false;
                }

                XYZ? tagPoint = null;

                if (elem.Location is LocationCurve lc && lc.Curve != null)
                {
                    Curve curve = lc.Curve;
                    if (curve.Length < minLenFt) return false;

                    XYZ midRaw = curve.Evaluate(0.5, true);
                    XYZ mid = tf.OfPoint(midRaw);

                    // Kiểm tra cao độ nằm trong khoảng tầng (dung sai ±0.3m)
                    double tolFt = 0.3 / 0.3048;
                    if (mid.Z < (minZFt - tolFt) || mid.Z > (maxZFt + tolFt))
                    {
                        return false;
                    }

                    // Kiểm tra khoảng cách với các tag đã đặt để tránh đè chữ
                    foreach (var pt in placedTagPoints)
                    {
                        double dx = mid.X - pt.X;
                        double dy = mid.Y - pt.Y;
                        if (Math.Sqrt(dx * dx + dy * dy) < minSpacingFt)
                        {
                            return false; // Quá gần tag khác, bỏ qua
                        }
                    }

                    string? cosLabel = trade.TagFormatter?.Invoke(elem, mid);
                    if (string.IsNullOrWhiteSpace(cosLabel)) return false;

                    var textNote = TextNote.Create(hostDoc, view.Id, mid, cosLabel, textTypeId);
                    if (textNote != null)
                    {
                        placedTagPoints.Add(mid);
                        return true;
                    }
                }
                else if (elem.Location is LocationPoint lp)
                {
                    XYZ ptRaw = lp.Point;
                    XYZ pt = tf.OfPoint(ptRaw);

                    double tolFt = 0.3 / 0.3048;
                    if (pt.Z < (minZFt - tolFt) || pt.Z > (maxZFt + tolFt))
                    {
                        return false;
                    }

                    foreach (var p in placedTagPoints)
                    {
                        double dx = pt.X - p.X;
                        double dy = pt.Y - p.Y;
                        if (Math.Sqrt(dx * dx + dy * dy) < minSpacingFt)
                        {
                            return false;
                        }
                    }

                    string? cosLabel = trade.TagFormatter?.Invoke(elem, pt);
                    if (string.IsNullOrWhiteSpace(cosLabel))
                    {
                        double clM = pt.Z * 0.3048;
                        string nameStr = elem.Name;
                        if (nameStr.Length > 20) nameStr = nameStr.Substring(0, 20);
                        cosLabel = $"{nameStr} • {FormatElevation(clM)}";
                    }

                    var textNote = TextNote.Create(hostDoc, view.Id, pt, cosLabel, textTypeId);
                    if (textNote != null)
                    {
                        placedTagPoints.Add(pt);
                        return true;
                    }
                }
            }
            catch { }

            return false;
        }

        private static string FormatElevation(double meters)
        {
            if (meters >= 0)
            {
                return $"+{meters:F3}";
            }
            return $"{meters:F3}";
        }

        private static string CleanFileName(string raw)
        {
            if (string.IsNullOrEmpty(raw)) return "Floor";
            string s = raw;
            foreach (char c in Path.GetInvalidFileNameChars())
            {
                s = s.Replace(c, '_');
            }
            return s.Replace(" ", "_").Trim();
        }
    }
}
