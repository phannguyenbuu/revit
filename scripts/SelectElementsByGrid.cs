using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    /// <summary>
    /// Hàm chọn đối tượng trong phạm vi lưới trục (Grids / Axes) trong Revit.
    /// Hỗ trợ lọc theo trục X, trục Y, từng tầng hoặc tất cả các tầng, lọc theo Category,
    /// và tự động highlight/select trực tiếp trên màn hình Revit UI.
    /// </summary>
    public static class SelectElementsByGrid
    {
        private const double FT_TO_MM = 304.8;
        private const double MM_TO_FT = 1.0 / 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null)
            {
                return new { success = false, message = "Không tìm thấy tài liệu Revit đang mở." };
            }

            // Nếu tham số được bọc trong thuộc tính "args", giải nén nó
            if (args.TryGetProperty("args", out var innerArgs) && innerArgs.ValueKind == JsonValueKind.Object)
            {
                args = innerArgs;
            }

            try
            {
                // 1. Phân tích tham số lưới trục (Grid X & Grid Y)
                var (minX, maxX, gridXDesc, gridsXResolved) = ResolveXBounds(doc, args);
                var (minY, maxY, gridYDesc, gridsYResolved) = ResolveYBounds(doc, args);

                // 2. Phân tích tham số tầng (Level)
                var (targetLevelIds, levelDesc) = ResolveLevels(doc, uidoc, args);

                // 3. Phân tích danh sách Category cần chọn
                var targetCategories = ResolveCategories(args);

                // 4. Lựa chọn các tùy chọn hiển thị / thao tác
                bool setSelection = true;
                if (args.TryGetProperty("setSelection", out var pSel))
                    setSelection = pSel.GetBoolean();

                bool zoomTo = false;
                if (args.TryGetProperty("zoomTo", out var pZoom))
                    zoomTo = pZoom.GetBoolean();

                bool isolate = false;
                if (args.TryGetProperty("isolate", out var pIso))
                    isolate = pIso.GetBoolean();

                string action = "select";
                if (args.TryGetProperty("action", out var pAct))
                    action = pAct.GetString()?.ToLowerInvariant() ?? "select";

                // 5. Thu thập và lọc các đối tượng trong mô hình
                var matchedElements = new List<Element>();
                var matchedIds = new List<ElementId>();

                foreach (var cat in targetCategories)
                {
                    var collector = new FilteredElementCollector(doc)
                        .OfCategory(cat)
                        .WhereElementIsNotElementType();

                    // Nếu có lọc tầng và category hỗ trợ lọc nhanh bằng LevelFilter
                    if (targetLevelIds != null && targetLevelIds.Count == 1 &&
                        (cat == BuiltInCategory.OST_Doors || cat == BuiltInCategory.OST_Windows || cat == BuiltInCategory.OST_Rooms))
                    {
                        collector.WherePasses(new ElementLevelFilter(targetLevelIds[0]));
                    }

                    var elements = collector.ToElements();

                    foreach (var elem in elements)
                    {
                        // Kiểm tra lọc tầng
                        if (targetLevelIds != null && targetLevelIds.Count > 0)
                        {
                            var elemLevelId = GetElementLevelId(doc, elem);
                            if (elemLevelId == ElementId.InvalidElementId || !targetLevelIds.Contains(elemLevelId))
                            {
                                continue;
                            }
                        }

                        // Kiểm tra tọa độ trong phạm vi [minX, maxX] và [minY, maxY]
                        if (IsElementInBounds(elem, minX, maxX, minY, maxY))
                        {
                            matchedElements.Add(elem);
                            matchedIds.Add(elem.Id);
                        }
                    }
                }

                // Loại bỏ trùng lặp nếu có
                matchedElements = matchedElements.GroupBy(e => e.Id.Value).Select(g => g.First()).ToList();
                matchedIds = matchedElements.Select(e => e.Id).ToList();

                // 6. Thực hiện hành động (Highlight trong UI, Zoom, Isolate, hoặc Thay đổi kiểu)
                string actionResultMsg = "";
                if (setSelection && uidoc != null)
                {
                    uidoc.Selection.SetElementIds(matchedIds);
                }

                if (zoomTo && uidoc != null && matchedIds.Count > 0)
                {
                    uidoc.ShowElements(matchedIds);
                }

                if (isolate && uidoc != null && uidoc.ActiveView != null && matchedIds.Count > 0)
                {
                    using (var txIso = new Transaction(doc, "AI: Cô lập đối tượng trong trục"))
                    {
                        txIso.Start();
                        uidoc.ActiveView.IsolateElementsTemporary(matchedIds);
                        txIso.Commit();
                    }
                }

                // Xử lý action đổi kiểu hoặc xóa nếu được yêu cầu
                if (action == "delete" && matchedIds.Count > 0)
                {
                    using (var txDel = new Transaction(doc, "AI: Xóa đối tượng trong trục"))
                    {
                        txDel.Start();
                        doc.Delete(matchedIds);
                        txDel.Commit();
                    }
                    actionResultMsg = $" Đã xóa {matchedIds.Count} đối tượng.";
                }

                // 7. Tạo danh sách kết quả chi tiết
                var elementDetails = new List<object>();
                foreach (var e in matchedElements)
                {
                    var lp = e.Location as LocationPoint;
                    var lc = e.Location as LocationCurve;
                    double xMm = 0, yMm = 0, zMm = 0;

                    if (lp != null)
                    {
                        xMm = Math.Round(lp.Point.X * FT_TO_MM, 1);
                        yMm = Math.Round(lp.Point.Y * FT_TO_MM, 1);
                        zMm = Math.Round(lp.Point.Z * FT_TO_MM, 1);
                    }
                    else if (lc != null)
                    {
                        var mid = (lc.Curve.GetEndPoint(0) + lc.Curve.GetEndPoint(1)) * 0.5;
                        xMm = Math.Round(mid.X * FT_TO_MM, 1);
                        yMm = Math.Round(mid.Y * FT_TO_MM, 1);
                        zMm = Math.Round(mid.Z * FT_TO_MM, 1);
                    }
                    else
                    {
                        var bb = e.get_BoundingBox(null);
                        if (bb != null)
                        {
                            xMm = Math.Round((bb.Min.X + bb.Max.X) * 0.5 * FT_TO_MM, 1);
                            yMm = Math.Round((bb.Min.Y + bb.Max.Y) * 0.5 * FT_TO_MM, 1);
                            zMm = Math.Round((bb.Min.Z + bb.Max.Z) * 0.5 * FT_TO_MM, 1);
                        }
                    }

                    string famName = "";
                    string typeName = "";
                    var symId = e.GetTypeId();
                    if (symId != ElementId.InvalidElementId)
                    {
                        var elemType = doc.GetElement(symId) as ElementType;
                        famName = elemType?.FamilyName ?? "";
                        typeName = elemType?.Name ?? "";
                    }

                    string mark = e.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.AsString() ?? "";
                    var lvlId = GetElementLevelId(doc, e);
                    string lvlName = lvlId != ElementId.InvalidElementId ? (doc.GetElement(lvlId) as Level)?.Name ?? "" : "";

                    elementDetails.Add(new
                    {
                        id = e.Id.Value,
                        category = e.Category?.Name ?? "Unknown",
                        family = famName,
                        type = typeName,
                        mark = mark,
                        level = lvlName,
                        x_mm = xMm,
                        y_mm = yMm,
                        z_mm = zMm
                    });
                }

                return new
                {
                    success = true,
                    message = $"Đã chọn {matchedElements.Count} đối tượng trong phạm vi {gridXDesc}, {gridYDesc} ({levelDesc}).{actionResultMsg}",
                    count = matchedElements.Count,
                    elementIds = matchedIds.Select(id => id.Value).ToList(),
                    grids = new
                    {
                        gridX = gridXDesc,
                        gridY = gridYDesc,
                        resolvedGridsX = gridsXResolved,
                        resolvedGridsY = gridsYResolved
                    },
                    bounds_mm = new
                    {
                        minX = Math.Round(minX, 1),
                        maxX = Math.Round(maxX, 1),
                        minY = Math.Round(minY, 1),
                        maxY = Math.Round(maxY, 1)
                    },
                    level = levelDesc,
                    elements = elementDetails
                };
            }
            catch (Exception ex)
            {
                return new { success = false, message = $"Lỗi xử lý chọn đối tượng: {ex.Message}", stack = ex.StackTrace };
            }
        }

        #region Helper: Bounds & Coordinates Resolution

        private static (double minX, double maxX, string desc, Dictionary<string, double> resolved) ResolveXBounds(Document doc, JsonElement args)
        {
            var resolved = new Dictionary<string, double>();
            double margin = 100.0; // mm
            if (args.TryGetProperty("marginX_mm", out var pMargin)) margin = pMargin.GetDouble();
            if (args.TryGetProperty("margin_mm", out var pMarginAll)) margin = pMarginAll.GetDouble();

            double tolerance = 1000.0; // mm (nếu chỉ chỉ định 1 trục)
            if (args.TryGetProperty("toleranceX_mm", out var pTol)) tolerance = pTol.GetDouble();
            if (args.TryGetProperty("tolerance_mm", out var pTolAll)) tolerance = pTolAll.GetDouble();

            // Kiểm tra chỉ định số trực tiếp
            if (args.TryGetProperty("minX_mm", out var pMinX) && args.TryGetProperty("maxX_mm", out var pMaxX))
            {
                double x1 = pMinX.GetDouble();
                double x2 = pMaxX.GetDouble();
                return (Math.Min(x1, x2) - margin, Math.Max(x1, x2) + margin, $"X=[{x1}, {x2}]mm", resolved);
            }

            // Đọc tên lưới trục X từ args
            var gridNames = ExtractStringList(args, "gridX", "gridXMin", "gridXMax", "gridsX");
            if (gridNames.Count == 0)
            {
                // Không giới hạn trục X
                return (double.MinValue / 2.0, double.MaxValue / 2.0, "toàn bộ trục X", resolved);
            }

            var allGrids = GetProjectGrids(doc);
            var xCoords = new List<double>();

            foreach (var gName in gridNames)
            {
                var grid = allGrids.FirstOrDefault(g => g.Name.Trim().Equals(gName.Trim(), StringComparison.OrdinalIgnoreCase));
                if (grid != null)
                {
                    double xCoord = GetGridCoordinate(grid, isVertical: true);
                    xCoords.Add(xCoord);
                    resolved[grid.Name] = Math.Round(xCoord, 1);
                }
            }

            if (xCoords.Count == 0)
            {
                return (double.MinValue / 2.0, double.MaxValue / 2.0, $"không tìm thấy trục X ({string.Join(", ", gridNames)})", resolved);
            }

            if (xCoords.Count == 1)
            {
                double x = xCoords[0];
                return (x - tolerance, x + tolerance, $"trục {gridNames[0]} (dung sai ±{tolerance}mm)", resolved);
            }

            double min = xCoords.Min() - margin;
            double max = xCoords.Max() + margin;
            return (min, max, $"giữa trục {gridNames.First()} và {gridNames.Last()}", resolved);
        }

        private static (double minY, double maxY, string desc, Dictionary<string, double> resolved) ResolveYBounds(Document doc, JsonElement args)
        {
            var resolved = new Dictionary<string, double>();
            double margin = 100.0; // mm
            if (args.TryGetProperty("marginY_mm", out var pMargin)) margin = pMargin.GetDouble();
            if (args.TryGetProperty("margin_mm", out var pMarginAll)) margin = pMarginAll.GetDouble();

            double tolerance = 1500.0; // mm (nếu chỉ chỉ định 1 trục, ví dụ trục C)
            if (args.TryGetProperty("toleranceY_mm", out var pTol)) tolerance = pTol.GetDouble();
            if (args.TryGetProperty("tolerance_mm", out var pTolAll)) tolerance = pTolAll.GetDouble();

            // Kiểm tra chỉ định số trực tiếp
            if (args.TryGetProperty("minY_mm", out var pMinY) && args.TryGetProperty("maxY_mm", out var pMaxY))
            {
                double y1 = pMinY.GetDouble();
                double y2 = pMaxY.GetDouble();
                return (Math.Min(y1, y2) - margin, Math.Max(y1, y2) + margin, $"Y=[{y1}, {y2}]mm", resolved);
            }

            // Đọc tên lưới trục Y từ args
            var gridNames = ExtractStringList(args, "gridY", "gridYMin", "gridYMax", "gridsY");
            if (gridNames.Count == 0)
            {
                // Không giới hạn trục Y
                return (double.MinValue / 2.0, double.MaxValue / 2.0, "toàn bộ trục Y", resolved);
            }

            var allGrids = GetProjectGrids(doc);
            var yCoords = new List<double>();

            foreach (var gName in gridNames)
            {
                var grid = allGrids.FirstOrDefault(g => g.Name.Trim().Equals(gName.Trim(), StringComparison.OrdinalIgnoreCase));
                if (grid != null)
                {
                    double yCoord = GetGridCoordinate(grid, isVertical: false);
                    yCoords.Add(yCoord);
                    resolved[grid.Name] = Math.Round(yCoord, 1);
                }
            }

            if (yCoords.Count == 0)
            {
                return (double.MinValue / 2.0, double.MaxValue / 2.0, $"không tìm thấy trục Y ({string.Join(", ", gridNames)})", resolved);
            }

            if (yCoords.Count == 1)
            {
                double y = yCoords[0];
                return (y - tolerance, y + tolerance, $"trục {gridNames[0]} (dung sai ±{tolerance}mm)", resolved);
            }

            double min = yCoords.Min() - margin;
            double max = yCoords.Max() + margin;
            return (min, max, $"giữa trục {gridNames.First()} và {gridNames.Last()}", resolved);
        }

        private static List<Grid> GetProjectGrids(Document doc)
        {
            return new FilteredElementCollector(doc)
                .OfClass(typeof(Grid))
                .Cast<Grid>()
                .ToList();
        }

        private static double GetGridCoordinate(Grid grid, bool isVertical)
        {
            var curve = grid.Curve;
            var p0 = curve.GetEndPoint(0);
            var p1 = curve.GetEndPoint(1);

            if (isVertical)
            {
                return ((p0.X + p1.X) * 0.5) * FT_TO_MM;
            }
            else
            {
                return ((p0.Y + p1.Y) * 0.5) * FT_TO_MM;
            }
        }

        private static List<string> ExtractStringList(JsonElement args, string singleKey, string minKey, string maxKey, string arrayKey)
        {
            var result = new List<string>();

            if (args.TryGetProperty(singleKey, out var pSingle))
            {
                if (pSingle.ValueKind == JsonValueKind.String)
                {
                    string s = pSingle.GetString() ?? "";
                    if (s.Contains("-") && !s.StartsWith("-"))
                    {
                        var parts = s.Split('-');
                        result.Add(parts[0].Trim());
                        result.Add(parts[1].Trim());
                    }
                    else if (s.Contains(","))
                    {
                        result.AddRange(s.Split(',').Select(x => x.Trim()).Where(x => !string.IsNullOrEmpty(x)));
                    }
                    else if (!string.IsNullOrWhiteSpace(s))
                    {
                        result.Add(s.Trim());
                    }
                }
                else if (pSingle.ValueKind == JsonValueKind.Array)
                {
                    foreach (var item in pSingle.EnumerateArray())
                    {
                        string s = item.GetString() ?? "";
                        if (!string.IsNullOrWhiteSpace(s)) result.Add(s.Trim());
                    }
                }
            }

            if (args.TryGetProperty(minKey, out var pMin))
            {
                string s = pMin.GetString() ?? "";
                if (!string.IsNullOrWhiteSpace(s) && !result.Contains(s.Trim())) result.Insert(0, s.Trim());
            }

            if (args.TryGetProperty(maxKey, out var pMax))
            {
                string s = pMax.GetString() ?? "";
                if (!string.IsNullOrWhiteSpace(s) && !result.Contains(s.Trim())) result.Add(s.Trim());
            }

            if (args.TryGetProperty(arrayKey, out var pArr) && pArr.ValueKind == JsonValueKind.Array)
            {
                foreach (var item in pArr.EnumerateArray())
                {
                    string s = item.GetString() ?? "";
                    if (!string.IsNullOrWhiteSpace(s) && !result.Contains(s.Trim())) result.Add(s.Trim());
                }
            }

            return result;
        }

        #endregion

        #region Helper: Level Resolution

        private static (List<ElementId>? levelIds, string desc) ResolveLevels(Document doc, UIDocument? uidoc, JsonElement args)
        {
            string levelQuery = "";
            if (args.TryGetProperty("level", out var pLvl))
            {
                levelQuery = pLvl.GetString()?.Trim() ?? "";
            }

            if (string.IsNullOrEmpty(levelQuery) || levelQuery.Equals("all", StringComparison.OrdinalIgnoreCase) || levelQuery.Equals("*"))
            {
                return (null, "tất cả các tầng");
            }

            var allLevels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .ToList();

            if (levelQuery.Equals("active", StringComparison.OrdinalIgnoreCase))
            {
                var activeView = uidoc?.ActiveView;
                var lvl = activeView?.GenLevel;
                if (lvl != null)
                {
                    return (new List<ElementId> { lvl.Id }, $"Tầng hiện hành ({lvl.Name})");
                }
            }

            // Tìm kiếm level theo tên hoặc viết tắt
            var matchedLevels = new List<Level>();
            string normQuery = NormalizeName(levelQuery);

            foreach (var lvl in allLevels)
            {
                string normLvlName = NormalizeName(lvl.Name);

                if (normLvlName.Contains(normQuery) || normQuery.Contains(normLvlName))
                {
                    matchedLevels.Add(lvl);
                }
                else if (IsLevelAliasMatch(normQuery, normLvlName))
                {
                    matchedLevels.Add(lvl);
                }
            }

            if (matchedLevels.Count > 0)
            {
                return (matchedLevels.Select(l => l.Id).ToList(), string.Join(", ", matchedLevels.Select(l => l.Name)));
            }

            // Thử kiểm tra nếu truyền Level ID
            if (long.TryParse(levelQuery, out long lvlIdVal))
            {
                var elemId = new ElementId(lvlIdVal);
                var lvl = doc.GetElement(elemId) as Level;
                if (lvl != null)
                {
                    return (new List<ElementId> { elemId }, lvl.Name);
                }
            }

            return (null, $"toàn bộ tầng (không tìm thấy tầng '{levelQuery}')");
        }

        private static bool IsLevelAliasMatch(string query, string levelNorm)
        {
            if (query == "1" || query == "tang1" || query == "tangtret")
                return levelNorm.Contains("tang1") || levelNorm.Contains("tret");
            if (query == "2" || query == "tang2")
                return levelNorm.Contains("tang2");
            if (query == "3" || query == "tang3")
                return levelNorm.Contains("tang3");
            if (query == "4" || query == "tang4")
                return levelNorm.Contains("tang4");
            if (query == "apmai" || query == "mai")
                return levelNorm.Contains("apmai") || levelNorm.Contains("mai");
            if (query == "tum" || query == "tangtum")
                return levelNorm.Contains("tum");
            if (query == "sanvuon" || query == "san")
                return levelNorm.Contains("sanvuon") || levelNorm.Contains("san");

            return false;
        }

        private static string NormalizeName(string text)
        {
            if (string.IsNullOrWhiteSpace(text)) return "";
            string normalizedString = text.Normalize(NormalizationForm.FormD);
            var stringBuilder = new StringBuilder();

            foreach (char c in normalizedString)
            {
                var unicodeCategory = CharUnicodeInfo.GetUnicodeCategory(c);
                if (unicodeCategory != UnicodeCategory.NonSpacingMark)
                {
                    if (char.IsLetterOrDigit(c))
                        stringBuilder.Append(char.ToLowerInvariant(c));
                }
            }

            return stringBuilder.ToString();
        }

        private static ElementId GetElementLevelId(Document doc, Element elem)
        {
            if (elem.LevelId != ElementId.InvalidElementId) return elem.LevelId;

            var pLvl = elem.get_Parameter(BuiltInParameter.FAMILY_LEVEL_PARAM)
                    ?? elem.get_Parameter(BuiltInParameter.SCHEDULE_LEVEL_PARAM)
                    ?? elem.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT)
                    ?? elem.get_Parameter(BuiltInParameter.LEVEL_PARAM)
                    ?? elem.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM)
                    ?? elem.get_Parameter(BuiltInParameter.INSTANCE_REFERENCE_LEVEL_PARAM);

            if (pLvl != null && pLvl.StorageType == StorageType.ElementId)
            {
                var id = pLvl.AsElementId();
                if (id != ElementId.InvalidElementId) return id;
            }

            return ElementId.InvalidElementId;
        }

        #endregion

        #region Helper: Categories Resolution

        private static List<BuiltInCategory> ResolveCategories(JsonElement args)
        {
            var requested = new List<string>();

            if (args.TryGetProperty("category", out var pCat))
            {
                if (pCat.ValueKind == JsonValueKind.String)
                {
                    string s = pCat.GetString() ?? "";
                    requested.AddRange(s.Split(',', ';').Select(x => x.Trim()));
                }
                else if (pCat.ValueKind == JsonValueKind.Array)
                {
                    foreach (var it in pCat.EnumerateArray())
                    {
                        string s = it.GetString() ?? "";
                        if (!string.IsNullOrWhiteSpace(s)) requested.Add(s.Trim());
                    }
                }
            }

            if (args.TryGetProperty("categories", out var pCats))
            {
                if (pCats.ValueKind == JsonValueKind.String)
                {
                    string s = pCats.GetString() ?? "";
                    requested.AddRange(s.Split(',', ';').Select(x => x.Trim()));
                }
                else if (pCats.ValueKind == JsonValueKind.Array)
                {
                    foreach (var it in pCats.EnumerateArray())
                    {
                        string s = it.GetString() ?? "";
                        if (!string.IsNullOrWhiteSpace(s)) requested.Add(s.Trim());
                    }
                }
            }

            var catSet = new HashSet<BuiltInCategory>();

            if (requested.Count == 0 || requested.Any(r => r.Equals("all", StringComparison.OrdinalIgnoreCase) || r.Equals("*")))
            {
                catSet.Add(BuiltInCategory.OST_Doors);
                catSet.Add(BuiltInCategory.OST_Windows);
                catSet.Add(BuiltInCategory.OST_Walls);
                catSet.Add(BuiltInCategory.OST_Columns);
                catSet.Add(BuiltInCategory.OST_StructuralColumns);
                catSet.Add(BuiltInCategory.OST_StructuralFraming);
                catSet.Add(BuiltInCategory.OST_Floors);
                catSet.Add(BuiltInCategory.OST_Rooms);
                catSet.Add(BuiltInCategory.OST_Furniture);
                catSet.Add(BuiltInCategory.OST_GenericModel);
                catSet.Add(BuiltInCategory.OST_PlumbingFixtures);
                catSet.Add(BuiltInCategory.OST_Stairs);
                catSet.Add(BuiltInCategory.OST_StairsRailing);
                return catSet.ToList();
            }

            foreach (var r in requested)
            {
                string key = NormalizeName(r);
                if (key.Contains("door") || key.Contains("cua") || key.Contains("cuadi"))
                    catSet.Add(BuiltInCategory.OST_Doors);
                else if (key.Contains("window") || key.Contains("cuaso"))
                    catSet.Add(BuiltInCategory.OST_Windows);
                else if (key.Contains("wall") || key.Contains("tuong"))
                    catSet.Add(BuiltInCategory.OST_Walls);
                else if (key.Contains("column") || key.Contains("cot"))
                {
                    catSet.Add(BuiltInCategory.OST_Columns);
                    catSet.Add(BuiltInCategory.OST_StructuralColumns);
                }
                else if (key.Contains("beam") || key.Contains("dam") || key.Contains("framing"))
                    catSet.Add(BuiltInCategory.OST_StructuralFraming);
                else if (key.Contains("floor") || key.Contains("san"))
                    catSet.Add(BuiltInCategory.OST_Floors);
                else if (key.Contains("room") || key.Contains("phong"))
                    catSet.Add(BuiltInCategory.OST_Rooms);
                else if (key.Contains("furniture") || key.Contains("noithat"))
                    catSet.Add(BuiltInCategory.OST_Furniture);
                else if (key.Contains("plumb") || key.Contains("vesinh") || key.Contains("wc"))
                    catSet.Add(BuiltInCategory.OST_PlumbingFixtures);
                else if (key.Contains("stair") || key.Contains("thang"))
                    catSet.Add(BuiltInCategory.OST_Stairs);
                else if (key.Contains("rail") || key.Contains("lancan"))
                    catSet.Add(BuiltInCategory.OST_StairsRailing);
                else if (key.Contains("generic"))
                    catSet.Add(BuiltInCategory.OST_GenericModel);
            }

            if (catSet.Count == 0) catSet.Add(BuiltInCategory.OST_Doors); // Mặc định nếu không nhận diện được
            return catSet.ToList();
        }

        #endregion

        #region Helper: Spatial Bounds Checking

        private static bool IsElementInBounds(Element elem, double minX, double maxX, double minY, double maxY)
        {
            // Trường hợp 1: Có LocationPoint (Doors, Windows, Columns, Furniture, Plumbing, v.v.)
            if (elem.Location is LocationPoint lp)
            {
                double x = lp.Point.X * FT_TO_MM;
                double y = lp.Point.Y * FT_TO_MM;
                return (x >= minX && x <= maxX && y >= minY && y <= maxY);
            }

            // Trường hợp 2: Có LocationCurve (Walls, Beams)
            if (elem.Location is LocationCurve lc)
            {
                var p0 = lc.Curve.GetEndPoint(0);
                var p1 = lc.Curve.GetEndPoint(1);
                double x0 = p0.X * FT_TO_MM, y0 = p0.Y * FT_TO_MM;
                double x1 = p1.X * FT_TO_MM, y1 = p1.Y * FT_TO_MM;
                double midX = (x0 + x1) * 0.5;
                double midY = (y0 + y1) * 0.5;

                // Trung điểm nằm trong vùng
                if (midX >= minX && midX <= maxX && midY >= minY && midY <= maxY)
                    return true;

                // Hoặc một trong hai đầu mút nằm trong vùng
                if ((x0 >= minX && x0 <= maxX && y0 >= minY && y0 <= maxY) ||
                    (x1 >= minX && x1 <= maxX && y1 >= minY && y1 <= maxY))
                    return true;

                // Hoặc đoạn thẳng cắt ngang hoàn toàn qua vùng BoundingBox
                double segMinX = Math.Min(x0, x1);
                double segMaxX = Math.Max(x0, x1);
                double segMinY = Math.Min(y0, y1);
                double segMaxY = Math.Max(y0, y1);

                if (segMinX <= maxX && segMaxX >= minX && segMinY <= maxY && segMaxY >= minY)
                    return true;

                return false;
            }

            // Trường hợp 3: Dùng BoundingBoxXYZ (Floors, Stairs, Generic Models, Rooms)
            var bb = elem.get_BoundingBox(null);
            if (bb != null)
            {
                double bbMinX = bb.Min.X * FT_TO_MM;
                double bbMaxX = bb.Max.X * FT_TO_MM;
                double bbMinY = bb.Min.Y * FT_TO_MM;
                double bbMaxY = bb.Max.Y * FT_TO_MM;

                double cenX = (bbMinX + bbMaxX) * 0.5;
                double cenY = (bbMinY + bbMaxY) * 0.5;

                if (cenX >= minX && cenX <= maxX && cenY >= minY && cenY <= maxY)
                    return true;

                if (bbMinX <= maxX && bbMaxX >= minX && bbMinY <= maxY && bbMaxY >= minY)
                    return true;
            }

            return false;
        }

        #endregion
    }
}
