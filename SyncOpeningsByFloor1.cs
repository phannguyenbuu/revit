using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class OpeningWarningSwallower : IFailuresPreprocessor
    {
        public FailureProcessingResult PreprocessFailures(FailuresAccessor failuresAccessor)
        {
            var msgs = failuresAccessor.GetFailureMessages();
            foreach (var m in msgs)
            {
                if (m.GetSeverity() == FailureSeverity.Warning)
                {
                    failuresAccessor.DeleteWarning(m);
                }
            }
            return FailureProcessingResult.Continue;
        }
    }

    public static class SyncOpeningsByFloor1
    {
        private const double FT_TO_MM = 304.8;
        private const double MM_TO_FT = 1.0 / 304.8;

        public class OpeningItem
        {
            public long Id { get; set; }
            public string Category { get; set; } = ""; // "Window" or "Door"
            public string Name { get; set; } = "";
            public string FamilyName { get; set; } = "";
            public string Mark { get; set; } = "";
            public string LevelName { get; set; } = "";
            public long LevelId { get; set; }
            public double LevelElevationMm { get; set; }
            public double X_mm { get; set; }
            public double Y_mm { get; set; }
            public double Z_mm { get; set; }
            public string WallAxis { get; set; } = ""; // Grid name or wall position
            public string Bay { get; set; } = "";      // Bay name e.g. "2-3" or "A-B"
            public bool IsFloor1 { get; set; }
            public double TargetCoord_mm { get; set; }
            public double DeltaCoord_mm { get; set; }
            public bool NeedsMove { get; set; }
            public bool Moved { get; set; }
            public string? Note { get; set; }
        }

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { success = false, error = "Không có tài liệu Revit nào đang mở!" };

            var targetArgs = args.ValueKind == JsonValueKind.Object && args.TryGetProperty("args", out var innerArgs) && innerArgs.ValueKind == JsonValueKind.Object ? innerArgs : args;

            // Đọc tham số
            string categoryChoice = "windows"; // "windows", "doors", or "all"
            string axisDirection = "X";        // "X" or "Y"
            string targetAxesFilter = "all";   // "all" or e.g. "A, E", "1, 11"
            bool applyMove = false;
            double toleranceMm = 1200.0;

            if (targetArgs.ValueKind == JsonValueKind.Object)
            {
                if (targetArgs.TryGetProperty("category", out var pCat)) categoryChoice = pCat.GetString()?.ToLower() ?? "windows";
                if (targetArgs.TryGetProperty("axisDirection", out var pDir)) axisDirection = pDir.GetString()?.ToUpper() ?? "X";
                if (targetArgs.TryGetProperty("targetAxes", out var pAxes)) targetAxesFilter = pAxes.GetString()?.Trim() ?? "all";
                if (targetArgs.TryGetProperty("apply", out var pApply)) applyMove = pApply.GetBoolean();
                if (targetArgs.TryGetProperty("toleranceMm", out var pTol)) toleranceMm = pTol.GetDouble();
            }

            bool syncX = (axisDirection == "X");

            // Tách danh sách targetAxes nếu có bộ lọc
            var allowedAxes = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            if (!string.IsNullOrEmpty(targetAxesFilter) && !targetAxesFilter.Equals("all", StringComparison.OrdinalIgnoreCase))
            {
                var parts = targetAxesFilter.Split(new char[] { ',', ';', ' ' }, StringSplitOptions.RemoveEmptyEntries);
                foreach (var p in parts) allowedAxes.Add(p.Trim());
            }

            // 1. Quét và phân loại tất cả các Trục (Grids)
            var grids = new FilteredElementCollector(doc)
                .OfClass(typeof(Grid))
                .Cast<Grid>()
                .ToList();

            var xGrids = new Dictionary<string, double>(); // Trục số (dọc theo Y, X cố định)
            var yGrids = new Dictionary<string, double>(); // Trục chữ (dọc theo X, Y cố định)

            foreach (var g in grids)
            {
                var curve = g.Curve;
                var pt0 = curve.GetEndPoint(0);
                var pt1 = curve.GetEndPoint(1);

                // Trục chạy dọc theo Y (X không đổi) -> Trục số định vị X
                if (Math.Abs(pt0.X - pt1.X) < 1.0)
                {
                    xGrids[g.Name.Trim()] = Math.Round(pt0.X * FT_TO_MM, 1);
                }
                // Trục chạy ngang theo X (Y không đổi) -> Trục chữ định vị Y
                else if (Math.Abs(pt0.Y - pt1.Y) < 1.0)
                {
                    yGrids[g.Name.Trim()] = Math.Round(pt0.Y * FT_TO_MM, 1);
                }
            }

            // Tạo các ô trục (Bays):
            // Nếu syncX == true: Các ô trục chạy dọc theo X được giới hạn bởi các trục số (1-2, 2-3, ...)
            // Nếu syncX == false: Các ô trục chạy dọc theo Y được giới hạn bởi các trục chữ (A-B, B-C, ...)
            var bays = new List<(string bayName, double minVal, double maxVal)>();

            if (syncX)
            {
                // Sắp xếp các trục X tăng dần
                var sortedX = xGrids.OrderBy(kv => kv.Value).ToList();
                for (int i = 0; i < sortedX.Count - 1; i++)
                {
                    string g1 = sortedX[i].Key;
                    string g2 = sortedX[i + 1].Key;
                    double x1 = sortedX[i].Value;
                    double x2 = sortedX[i + 1].Value;
                    bays.Add(($"{g1}-{g2}", Math.Min(x1, x2), Math.Max(x1, x2)));
                }
            }
            else
            {
                // Sắp xếp các trục Y tăng dần
                var sortedY = yGrids.OrderBy(kv => kv.Value).ToList();
                for (int i = 0; i < sortedY.Count - 1; i++)
                {
                    string g1 = sortedY[i].Key;
                    string g2 = sortedY[i + 1].Key;
                    double y1 = sortedY[i].Value;
                    double y2 = sortedY[i + 1].Value;
                    bays.Add(($"{g1}-{g2}", Math.Min(y1, y2), Math.Max(y1, y2)));
                }
            }

            // 2. Quét các Level và tìm Floor 1
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .OrderBy(l => l.Elevation)
                .ToList();

            var levelMap = new Dictionary<long, (string name, double elevMm)>();
            long floor1LevelId = -1;
            foreach (var l in levels)
            {
                double elevMm = Math.Round(l.Elevation * FT_TO_MM, 1);
                levelMap[l.Id.Value] = (l.Name, elevMm);

                if (l.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase) ||
                    l.Name.Contains("TANG 1", StringComparison.OrdinalIgnoreCase) ||
                    l.Name.Contains("01.", StringComparison.OrdinalIgnoreCase))
                {
                    floor1LevelId = l.Id.Value;
                }
            }

            if (floor1LevelId == -1 && levels.Count > 0)
            {
                var f1 = levels.FirstOrDefault(l => l.Elevation >= -0.1) ?? levels[0];
                floor1LevelId = f1.Id.Value;
            }

            // 3. Thu thập các đối tượng (Cửa sổ / Cửa đi)
            var targetInstances = new List<FamilyInstance>();

            if (categoryChoice == "windows" || categoryChoice == "all")
            {
                var wins = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Windows)
                    .WhereElementIsNotElementType()
                    .Cast<FamilyInstance>();
                targetInstances.AddRange(wins);
            }

            if (categoryChoice == "doors" || categoryChoice == "all")
            {
                var drs = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Doors)
                    .WhereElementIsNotElementType()
                    .Cast<FamilyInstance>();
                targetInstances.AddRange(drs);
            }

            var openingItems = new List<OpeningItem>();

            foreach (var inst in targetInstances)
            {
                var lp = inst.Location as LocationPoint;
                if (lp == null) continue;

                double x = Math.Round(lp.Point.X * FT_TO_MM, 1);
                double y = Math.Round(lp.Point.Y * FT_TO_MM, 1);
                double z = Math.Round(lp.Point.Z * FT_TO_MM, 1);

                // Xác định Level
                long lvlId = -1;
                string lvlName = "Không xác định";
                double lvlElev = 0;
                if (inst.LevelId != null && inst.LevelId != ElementId.InvalidElementId && levelMap.ContainsKey(inst.LevelId.Value))
                {
                    lvlId = inst.LevelId.Value;
                    lvlName = levelMap[lvlId].name;
                    lvlElev = levelMap[lvlId].elevMm;
                }
                else if (inst.Host is Wall w)
                {
                    var pLvl = w.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT)?.AsElementId();
                    if (pLvl != null && levelMap.ContainsKey(pLvl.Value))
                    {
                        lvlId = pLvl.Value;
                        lvlName = levelMap[lvlId].name;
                        lvlElev = levelMap[lvlId].elevMm;
                    }
                }

                bool isF1 = (lvlId == floor1LevelId) || lvlName.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase) || Math.Abs(lvlElev) < 500.0;

                string wallAxis = "";
                string bayName = "";

                if (syncX)
                {
                    // Tường ngang: Tìm trục chữ (Y grid) gần nhất
                    double minDiffY = double.MaxValue;
                    string bestYGrid = "";
                    foreach (var yg in yGrids)
                    {
                        double diff = Math.Abs(y - yg.Value);
                        if (diff < minDiffY)
                        {
                            minDiffY = diff;
                            bestYGrid = yg.Key;
                        }
                    }

                    if (minDiffY <= toleranceMm)
                    {
                        wallAxis = bestYGrid;
                    }
                    else
                    {
                        // Nhóm theo cao độ Y xấp xỉ
                        double roundY = Math.Round(y / 500.0) * 500.0;
                        wallAxis = $"Y_{roundY:0}";
                    }

                    // Tìm ô trục X (Bay)
                    foreach (var b in bays)
                    {
                        if (x >= b.minVal - 50.0 && x <= b.maxVal + 50.0)
                        {
                            bayName = b.bayName;
                            break;
                        }
                    }
                }
                else
                {
                    // Tường dọc: Tìm trục số (X grid) gần nhất
                    double minDiffX = double.MaxValue;
                    string bestXGrid = "";
                    foreach (var xg in xGrids)
                    {
                        double diff = Math.Abs(x - xg.Value);
                        if (diff < minDiffX)
                        {
                            minDiffX = diff;
                            bestXGrid = xg.Key;
                        }
                    }

                    if (minDiffX <= toleranceMm)
                    {
                        wallAxis = bestXGrid;
                    }
                    else
                    {
                        double roundX = Math.Round(x / 500.0) * 500.0;
                        wallAxis = $"X_{roundX:0}";
                    }

                    // Tìm ô trục Y (Bay)
                    foreach (var b in bays)
                    {
                        if (y >= b.minVal - 50.0 && y <= b.maxVal + 50.0)
                        {
                            bayName = b.bayName;
                            break;
                        }
                    }
                }

                if (string.IsNullOrEmpty(bayName)) continue;

                // Lọc theo targetAxes nếu có
                if (allowedAxes.Count > 0 && !allowedAxes.Contains(wallAxis))
                {
                    continue;
                }

                string catName = inst.Category?.Name ?? (inst is FamilyInstance ? "Opening" : "");
                string mark = inst.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.AsString() ?? "";
                string typeName = inst.Symbol?.Name ?? "";
                string famName = inst.Symbol?.Family?.Name ?? "";

                openingItems.Add(new OpeningItem
                {
                    Id = inst.Id.Value,
                    Category = catName,
                    Name = typeName,
                    FamilyName = famName,
                    Mark = mark,
                    LevelName = lvlName,
                    LevelId = lvlId,
                    LevelElevationMm = lvlElev,
                    X_mm = x,
                    Y_mm = y,
                    Z_mm = z,
                    WallAxis = wallAxis,
                    Bay = bayName,
                    IsFloor1 = isF1
                });
            }

            // 4. Nhóm theo (WallAxis, Bay) và tính toán độ dịch chuyển
            var grouped = openingItems
                .GroupBy(it => $"{it.WallAxis}_{it.Bay}")
                .ToList();

            var planUpdates = new List<OpeningItem>();
            var noF1Groups = new List<string>();

            foreach (var g in grouped)
            {
                var list = g.ToList();
                var f1List = list.Where(it => it.IsFloor1).ToList();
                var upperList = list.Where(it => !it.IsFloor1).ToList();

                if (f1List.Count == 0)
                {
                    noF1Groups.Add(g.Key);
                    continue;
                }

                // Sắp xếp theo tọa độ đồng bộ (X hoặc Y)
                if (syncX)
                {
                    f1List = f1List.OrderBy(it => it.X_mm).ToList();
                }
                else
                {
                    f1List = f1List.OrderBy(it => it.Y_mm).ToList();
                }

                // Nhóm tầng trên theo từng Level
                var upperByLevel = upperList.GroupBy(it => it.LevelId);

                foreach (var lvlGroup in upperByLevel)
                {
                    var uList = syncX
                        ? lvlGroup.OrderBy(it => it.X_mm).ToList()
                        : lvlGroup.OrderBy(it => it.Y_mm).ToList();

                    for (int i = 0; i < uList.Count; i++)
                    {
                        var uItem = uList[i];
                        double targetCoord;

                        // Ghép đôi 1-to-1 theo thứ tự nếu số lượng bằng nhau
                        if (uList.Count == f1List.Count)
                        {
                            targetCoord = syncX ? f1List[i].X_mm : f1List[i].Y_mm;
                        }
                        else
                        {
                            // Tìm phần tử Tầng 1 gần nhất theo tọa độ
                            if (syncX)
                            {
                                targetCoord = f1List.OrderBy(f => Math.Abs(f.X_mm - uItem.X_mm)).First().X_mm;
                            }
                            else
                            {
                                targetCoord = f1List.OrderBy(f => Math.Abs(f.Y_mm - uItem.Y_mm)).First().Y_mm;
                            }
                        }

                        double currentCoord = syncX ? uItem.X_mm : uItem.Y_mm;
                        double delta = Math.Round(targetCoord - currentCoord, 1);

                        uItem.TargetCoord_mm = targetCoord;
                        uItem.DeltaCoord_mm = delta;
                        uItem.NeedsMove = (Math.Abs(delta) >= 1.0);

                        planUpdates.Add(uItem);
                    }
                }
            }

            // 5. Thực thi di chuyển (nếu applyMove == true)
            int movedCount = 0;
            var moveErrors = new List<string>();

            if (applyMove && planUpdates.Count > 0)
            {
                using (var tx = new Transaction(doc, $"Đồng bộ Cửa các tầng theo Tầng 1 (Trục {axisDirection})"))
                {
                    var opt = tx.GetFailureHandlingOptions();
                    opt.SetFailuresPreprocessor(new OpeningWarningSwallower());
                    tx.SetFailureHandlingOptions(opt);
                    tx.Start();

                    foreach (var info in planUpdates)
                    {
                        if (!info.NeedsMove)
                        {
                            info.Note = "Đã khớp vị trí, không cần di chuyển.";
                            continue;
                        }

                        var elem = doc.GetElement(new ElementId(info.Id));
                        if (elem != null)
                        {
                            try
                            {
                                XYZ moveVec = syncX
                                    ? new XYZ(info.DeltaCoord_mm * MM_TO_FT, 0, 0)
                                    : new XYZ(0, info.DeltaCoord_mm * MM_TO_FT, 0);

                                ElementTransformUtils.MoveElement(doc, elem.Id, moveVec);
                                info.Moved = true;
                                info.Note = $"Đã dịch chuyển {info.DeltaCoord_mm:F1} mm dọc trục {axisDirection}.";
                                movedCount++;
                            }
                            catch (Exception ex)
                            {
                                info.Note = "Lỗi khi di chuyển: " + ex.Message;
                                moveErrors.Add($"ID {info.Id}: {ex.Message}");
                            }
                        }
                    }

                    doc.Regenerate();
                    tx.Commit();
                }
            }

            int needMoveCount = planUpdates.Count(p => p.NeedsMove);

            string summaryMsg = applyMove
                ? $"ĐÃ ĐỒNG BỘ: Hoàn tất dịch chuyển {movedCount}/{needMoveCount} vị trí cửa tầng trên theo Tầng 1 (Phương {axisDirection})."
                : $"XEM TRƯỚC: Tìm thấy {openingItems.Count} cửa (Tầng 1: {openingItems.Count(it => it.IsFloor1)}, Tầng trên: {openingItems.Count(it => !it.IsFloor1)}). Có {needMoveCount} cửa cần dịch chuyển theo Tầng 1.";

            return new
            {
                success = true,
                apply = applyMove,
                category = categoryChoice,
                axisDirection,
                targetAxesFilter,
                totalFound = openingItems.Count,
                floor1Count = openingItems.Count(it => it.IsFloor1),
                upperCount = openingItems.Count(it => !it.IsFloor1),
                needsMoveCount = needMoveCount,
                movedCount,
                moveErrors,
                noF1Groups,
                message = summaryMsg,
                details = planUpdates.Select(u => new
                {
                    id = u.Id,
                    category = u.Category,
                    axis = u.WallAxis,
                    bay = u.Bay,
                    level = u.LevelName,
                    mark = u.Mark,
                    name = u.Name,
                    current = syncX ? u.X_mm : u.Y_mm,
                    target = u.TargetCoord_mm,
                    delta = u.DeltaCoord_mm,
                    needsMove = u.NeedsMove,
                    moved = u.Moved,
                    note = u.Note
                }).ToList()
            };
        }
    }
}
