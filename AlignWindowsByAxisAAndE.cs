using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class AlignWindowsByAxisAAndE
    {
        private const double FT_TO_MM = 304.8;
        private const double MM_TO_FT = 1.0 / 304.8;

        public class WindowInfo
        {
            public long Id { get; set; }
            public string Name { get; set; } = "";
            public string FamilyName { get; set; } = "";
            public string Mark { get; set; } = "";
            public string LevelName { get; set; } = "";
            public long LevelId { get; set; }
            public double LevelElevationMm { get; set; }
            public double X_mm { get; set; }
            public double Y_mm { get; set; }
            public double Z_mm { get; set; }
            public string Axis { get; set; } = ""; // "A" or "E"
            public string Bay { get; set; } = "";  // "2-3", "3-4", etc.
            public int BayIndex { get; set; }
            public bool IsFloor1 { get; set; }
            public double TargetX_mm { get; set; }
            public double DeltaX_mm { get; set; }
            public bool Moved { get; set; }
            public string? Note { get; set; }
        }

        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { success = false, error = "Không có tài liệu Revit nào đang mở!" };

            bool applyMove = false;
            if (args.ValueKind == System.Text.Json.JsonValueKind.Object)
            {
                if (args.TryGetProperty("apply", out var pApply)) applyMove = pApply.GetBoolean();
            }

            // 1. Lấy tọa độ các trục X (1..11) và trục Y (A, E)
            var grids = new FilteredElementCollector(doc)
                .OfClass(typeof(Grid))
                .Cast<Grid>()
                .ToList();

            var xGrids = new Dictionary<string, double>();
            var yGrids = new Dictionary<string, double>();

            foreach (var g in grids)
            {
                var curve = g.Curve;
                var pt0 = curve.GetEndPoint(0);
                var pt1 = curve.GetEndPoint(1);

                // Nếu trục chạy dọc theo Y (X gần như không đổi) -> Trục số (X grids)
                if (Math.Abs(pt0.X - pt1.X) < 1.0)
                {
                    xGrids[g.Name.Trim()] = Math.Round(pt0.X * FT_TO_MM, 1);
                }
                // Nếu trục chạy ngang theo X (Y gần như không đổi) -> Trục chữ (Y grids)
                else if (Math.Abs(pt0.Y - pt1.Y) < 1.0)
                {
                    yGrids[g.Name.Trim()] = Math.Round(pt0.Y * FT_TO_MM, 1);
                }
            }

            double yA = yGrids.ContainsKey("A") ? yGrids["A"] : 0.0;
            double yE = yGrids.ContainsKey("E") ? yGrids["E"] : 14900.0;

            // Định nghĩa các ô trục từ trục 2 đến trục 11
            string[] gridOrder = new string[] { "2", "3", "4", "5", "6", "7", "8", "9", "10", "11" };
            var bays = new List<(string bayName, int index, double minX, double maxX)>();
            for (int i = 0; i < gridOrder.Length - 1; i++)
            {
                string g1 = gridOrder[i];
                string g2 = gridOrder[i + 1];
                if (xGrids.ContainsKey(g1) && xGrids.ContainsKey(g2))
                {
                    double x1 = xGrids[g1];
                    double x2 = xGrids[g2];
                    double min = Math.Min(x1, x2);
                    double max = Math.Max(x1, x2);
                    bays.Add(($"{g1}-{g2}", i + 1, min, max));
                }
            }

            double xMinOverall = xGrids.ContainsKey("2") ? xGrids["2"] - 200 : 4150.0;
            double xMaxOverall = xGrids.ContainsKey("11") ? xGrids["11"] + 200 : 37350.0;

            // 2. Lấy thông tin các Level
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

                // Nhận diện Tầng 1
                if (l.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase) ||
                    l.Name.Contains("TANG 1", StringComparison.OrdinalIgnoreCase) ||
                    l.Name.Contains("01.", StringComparison.OrdinalIgnoreCase))
                {
                    floor1LevelId = l.Id.Value;
                }
            }

            // Fallback nếu không khớp tên: Level có cao độ dương thấp nhất (sau sân vườn)
            if (floor1LevelId == -1 && levels.Count > 0)
            {
                var f1 = levels.FirstOrDefault(l => l.Elevation >= -0.1) ?? levels[0];
                floor1LevelId = f1.Id.Value;
            }

            // 3. Lấy tất cả cửa sổ trong dự án (OST_Windows)
            var allWindows = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Windows)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .ToList();

            var targetWindows = new List<WindowInfo>();

            foreach (var win in allWindows)
            {
                var lp = win.Location as LocationPoint;
                if (lp == null) continue;

                double x = Math.Round(lp.Point.X * FT_TO_MM, 1);
                double y = Math.Round(lp.Point.Y * FT_TO_MM, 1);
                double z = Math.Round(lp.Point.Z * FT_TO_MM, 1);

                // Kiểm tra phạm vi X: từ trục 2 đến trục 11
                if (x < xMinOverall || x > xMaxOverall) continue;

                // Xác định xem thuộc trục A hay trục E
                string axis = "";
                if (Math.Abs(y - yA) <= 1200.0) axis = "A";
                else if (Math.Abs(y - yE) <= 1200.0) axis = "E";
                else continue;

                // Xác định ô trục X (Bay 2-3, 3-4, ...)
                string bayName = "";
                int bayIdx = -1;
                foreach (var b in bays)
                {
                    // Chấp nhận dung sai 50mm tại biên
                    if (x >= b.minX - 50.0 && x <= b.maxX + 50.0)
                    {
                        bayName = b.bayName;
                        bayIdx = b.index;
                        break;
                    }
                }

                if (string.IsNullOrEmpty(bayName)) continue;

                // Xác định Level
                long lvlId = -1;
                string lvlName = "Không xác định";
                double lvlElev = 0;
                if (win.LevelId != null && win.LevelId != ElementId.InvalidElementId && levelMap.ContainsKey(win.LevelId.Value))
                {
                    lvlId = win.LevelId.Value;
                    lvlName = levelMap[lvlId].name;
                    lvlElev = levelMap[lvlId].elevMm;
                }
                else if (win.Host is Wall w)
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

                string mark = win.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.AsString() ?? "";
                string typeName = win.Symbol?.Name ?? "";
                string famName = win.Symbol?.Family?.Name ?? "";

                targetWindows.Add(new WindowInfo
                {
                    Id = win.Id.Value,
                    Name = typeName,
                    FamilyName = famName,
                    Mark = mark,
                    LevelName = lvlName,
                    LevelId = lvlId,
                    LevelElevationMm = lvlElev,
                    X_mm = x,
                    Y_mm = y,
                    Z_mm = z,
                    Axis = axis,
                    Bay = bayName,
                    BayIndex = bayIdx,
                    IsFloor1 = isF1
                });
            }

            // 4. Nhóm theo Axis ("A", "E") và theo Bay ("2-3", "3-4", ...)
            var grouped = targetWindows
                .GroupBy(w => $"{w.Axis}_{w.Bay}")
                .ToList();

            var planUpdates = new List<WindowInfo>();
            var unmatchedUpper = new List<WindowInfo>();
            var noF1Bays = new List<string>();

            foreach (var g in grouped)
            {
                var list = g.ToList();
                var f1Windows = list.Where(w => w.IsFloor1).OrderBy(w => w.X_mm).ToList();
                var upperWindows = list.Where(w => !w.IsFloor1).OrderBy(w => w.LevelElevationMm).ThenBy(w => w.X_mm).ToList();

                if (f1Windows.Count == 0)
                {
                    noF1Bays.Add(g.Key);
                    continue;
                }

                // Trường hợp 1: Có đúng 1 cửa sổ ở Tầng 1 trong ô trục này
                if (f1Windows.Count == 1)
                {
                    double baseTargetX = f1Windows[0].X_mm;
                    foreach (var uw in upperWindows)
                    {
                        uw.TargetX_mm = baseTargetX;
                        uw.DeltaX_mm = Math.Round(baseTargetX - uw.X_mm, 1);
                        planUpdates.Add(uw);
                    }
                }
                // Trường hợp 2: Có nhiều hơn 1 cửa sổ ở Tầng 1 trong ô trục này (ghép cặp gần nhất)
                else
                {
                    // Với từng tầng trên, ghép cặp cửa sổ tầng trên với cửa sổ tầng 1 gần nó nhất về tọa độ X
                    var upperByLevel = upperWindows.GroupBy(w => w.LevelId);
                    foreach (var lvlGroup in upperByLevel)
                    {
                        var uList = lvlGroup.OrderBy(w => w.X_mm).ToList();
                        for (int i = 0; i < uList.Count; i++)
                        {
                            var uw = uList[i];
                            // Ghép theo thứ tự index nếu số lượng bằng nhau, hoặc lấy cửa sổ F1 gần nhất
                            double targetX;
                            if (uList.Count == f1Windows.Count)
                            {
                                targetX = f1Windows[i].X_mm;
                            }
                            else
                            {
                                targetX = f1Windows.OrderBy(f => Math.Abs(f.X_mm - uw.X_mm)).First().X_mm;
                            }

                            uw.TargetX_mm = targetX;
                            uw.DeltaX_mm = Math.Round(targetX - uw.X_mm, 1);
                            planUpdates.Add(uw);
                        }
                    }
                }
            }

            // 5. Nếu apply == true, thực thi di chuyển vị trí X
            int movedCount = 0;
            var moveErrors = new List<string>();

            if (applyMove && planUpdates.Count > 0)
            {
                using (var tx = new Transaction(doc, "Căn chỉnh trục X cửa sổ các tầng theo Tầng 1"))
                {
                    tx.Start();

                    foreach (var info in planUpdates)
                    {
                        if (Math.Abs(info.DeltaX_mm) < 1.0)
                        {
                            info.Note = "Đã chuẩn trục X, không cần dịch chuyển.";
                            continue;
                        }

                        var elem = doc.GetElement(new ElementId(info.Id));
                        if (elem != null)
                        {
                            try
                            {
                                double dxFt = info.DeltaX_mm * MM_TO_FT;
                                ElementTransformUtils.MoveElement(doc, elem.Id, new XYZ(dxFt, 0, 0));
                                info.Moved = true;
                                info.Note = $"Đã dịch chuyển {info.DeltaX_mm:F1} mm";
                                movedCount++;
                            }
                            catch (Exception ex)
                            {
                                info.Note = "Lỗi khi di chuyển: " + ex.Message;
                                moveErrors.Add($"Window {info.Id}: {ex.Message}");
                            }
                        }
                    }

                    tx.Commit();
                }
            }

            return new
            {
                success = true,
                applyMove,
                totalWindowsFound = targetWindows.Count,
                floor1WindowsCount = targetWindows.Count(w => w.IsFloor1),
                upperWindowsCount = targetWindows.Count(w => !w.IsFloor1),
                planUpdatesCount = planUpdates.Count,
                windowsNeedMove = planUpdates.Count(w => Math.Abs(w.DeltaX_mm) >= 1.0),
                movedCount,
                moveErrors,
                noF1Bays,
                details = planUpdates.Select(u => new {
                    id = u.Id,
                    axis = u.Axis,
                    bay = u.Bay,
                    level = u.LevelName,
                    mark = u.Mark,
                    name = u.Name,
                    currentX = u.X_mm,
                    targetX = u.TargetX_mm,
                    deltaX = u.DeltaX_mm,
                    moved = u.Moved,
                    note = u.Note
                }).ToList()
            };
        }
    }
}
