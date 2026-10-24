using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class SlabWarningSwallower : IFailuresPreprocessor
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

    public static class CreateOrReplaceSlabFromCad
    {
        private const double MM_TO_FT = 1.0 / 304.8;
        private const double FT_TO_MM = 304.8;
        private const double SQFT_TO_SQM = 0.09290304;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { success = false, error = "Không có tài liệu Revit nào đang mở!" };

            var targetArgs = args.ValueKind == JsonValueKind.Object && args.TryGetProperty("args", out var innerArgs) && innerArgs.ValueKind == JsonValueKind.Object ? innerArgs : args;

            bool checkRevitOnly = false;
            string floorCategory = "standard"; // "standard" or "toilet"
            double thicknessMm = 100.0;
            double offsetMm = 0.0;
            long levelId = -1;

            if (targetArgs.ValueKind == JsonValueKind.Object)
            {
                if (targetArgs.TryGetProperty("checkRevitOnly", out var pCheck)) checkRevitOnly = pCheck.GetBoolean();
                if (targetArgs.TryGetProperty("floorCategory", out var pCat)) floorCategory = pCat.GetString() ?? floorCategory;
                if (targetArgs.TryGetProperty("thicknessMm", out var pThick)) thicknessMm = pThick.GetDouble();
                if (targetArgs.TryGetProperty("offsetMm", out var pOff)) offsetMm = pOff.GetDouble();
                if (targetArgs.TryGetProperty("levelId", out var pLvl)) levelId = pLvl.GetInt64();
            }

            // 1. Kiểm tra xem Revit có đang chọn Sàn (Floor) không
            var selIds = uidoc.Selection.GetElementIds();
            Floor? selectedFloor = null;
            if (selIds != null && selIds.Count > 0)
            {
                foreach (var id in selIds)
                {
                    var elem = doc.GetElement(id);
                    if (elem is Floor f)
                    {
                        selectedFloor = f;
                        break;
                    }
                }
            }

            // Lấy Level của View hiện tại
            Level? activeViewLevel = null;
            if (uidoc.ActiveView is ViewPlan vp && vp.GenLevel != null)
            {
                activeViewLevel = vp.GenLevel;
            }

            // Nếu chỉ kiểm tra trạng thái Revit:
            if (checkRevitOnly)
            {
                if (selectedFloor != null)
                {
                    var ft = selectedFloor.FloorType;
                    var lvl = doc.GetElement(selectedFloor.LevelId) as Level;
                    var pOffset = selectedFloor.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM);
                    double curOffMm = pOffset != null ? Math.Round(pOffset.AsDouble() * FT_TO_MM, 1) : 0.0;

                    return new
                    {
                        success = true,
                        hasSelectedSlab = true,
                        slabId = selectedFloor.Id.Value,
                        slabTypeName = ft?.Name ?? "Floor",
                        levelId = selectedFloor.LevelId.Value,
                        levelName = lvl?.Name ?? "Unknown Level",
                        heightOffsetMm = curOffMm,
                        message = $"Đang chọn Sàn ID {selectedFloor.Id.Value} ({ft?.Name}) tại {lvl?.Name}. Sẽ THAY THẾ sàn này."
                    };
                }
                else
                {
                    return new
                    {
                        success = true,
                        hasSelectedSlab = false,
                        levelId = activeViewLevel?.Id.Value ?? -1,
                        levelName = activeViewLevel?.Name ?? "Tự động chọn tầng",
                        message = "Chưa chọn sàn nào trong Revit. Sẽ TẠO MỚI sàn theo cao độ tầng chỉ định."
                    };
                }
            }

            // 2. Đọc danh sách các vòng khép kín (Loops) từ CAD
            var loopsData = new List<List<(double x, double y)>>();
            if (targetArgs.TryGetProperty("loops", out var pLoops) && pLoops.ValueKind == JsonValueKind.Array)
            {
                for (int i = 0; i < pLoops.GetArrayLength(); i++)
                {
                    var loopElem = pLoops[i];
                    if (loopElem.ValueKind == JsonValueKind.Array)
                    {
                        var ptList = new List<(double x, double y)>();
                        for (int j = 0; j < loopElem.GetArrayLength(); j++)
                        {
                            var ptElem = loopElem[j];
                            if (ptElem.TryGetProperty("x", out var px) && ptElem.TryGetProperty("y", out var py))
                            {
                                ptList.Add((px.GetDouble(), py.GetDouble()));
                            }
                        }
                        if (ptList.Count >= 3) loopsData.Add(ptList);
                    }
                }
            }

            if (loopsData.Count == 0)
            {
                return new { success = false, error = "Không nhận được tọa độ đường bao (CurveLoop) hợp lệ từ AutoCAD!" };
            }

            // 3. Xác định Target Level
            ElementId targetLevelId = ElementId.InvalidElementId;
            string targetLevelName = "";

            if (selectedFloor != null && levelId == -1)
            {
                targetLevelId = selectedFloor.LevelId;
                targetLevelName = (doc.GetElement(targetLevelId) as Level)?.Name ?? "";
            }
            else if (levelId != -1)
            {
                var lvlElem = doc.GetElement(new ElementId(levelId)) as Level;
                if (lvlElem != null)
                {
                    targetLevelId = lvlElem.Id;
                    targetLevelName = lvlElem.Name;
                }
            }

            if (targetLevelId == ElementId.InvalidElementId && activeViewLevel != null)
            {
                targetLevelId = activeViewLevel.Id;
                targetLevelName = activeViewLevel.Name;
            }

            if (targetLevelId == ElementId.InvalidElementId)
            {
                var firstLvl = new FilteredElementCollector(doc)
                    .OfClass(typeof(Level))
                    .Cast<Level>()
                    .OrderBy(l => l.Elevation)
                    .FirstOrDefault(l => l.Elevation >= -1.0) ?? new FilteredElementCollector(doc).OfClass(typeof(Level)).Cast<Level>().First();
                targetLevelId = firstLvl.Id;
                targetLevelName = firstLvl.Name;
            }

            // 4. Xác định hoặc tạo mới FloorType tương ứng
            FloorType? targetFloorType = null;
            bool isToilet = floorCategory.Equals("toilet", StringComparison.OrdinalIgnoreCase);

            using (var txType = new Transaction(doc, "Ensure FloorType for CAD Slab"))
            {
                var opt = txType.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new SlabWarningSwallower());
                txType.SetFailureHandlingOptions(opt);
                txType.Start();

                if (isToilet)
                {
                    string ftName = $"NỀN WC {thicknessMm:0}mm";
                    targetFloorType = new FilteredElementCollector(doc)
                        .OfClass(typeof(FloorType))
                        .Cast<FloorType>()
                        .FirstOrDefault(f => f.Name.Equals(ftName, StringComparison.OrdinalIgnoreCase));

                    if (targetFloorType == null)
                    {
                        var baseFt = doc.GetElement(new ElementId(107061L)) as FloorType // NỀN WC
                            ?? new FilteredElementCollector(doc).OfClass(typeof(FloorType)).Cast<FloorType>().FirstOrDefault(f => f.Name.Contains("WC"))
                            ?? new FilteredElementCollector(doc).OfClass(typeof(FloorType)).Cast<FloorType>().First();

                        targetFloorType = (FloorType)baseFt.Duplicate(ftName);

                        var cs = targetFloorType.GetCompoundStructure();
                        int structIdx = cs.StructuralMaterialIndex;
                        if (structIdx < 0) structIdx = 0;
                        cs.SetLayerWidth(structIdx, thicknessMm * MM_TO_FT);
                        targetFloorType.SetCompoundStructure(cs);
                    }

                    // Đảm bảo Pattern ANGLE (Hatch gạch nghiêng 45 độ) tồn tại và gán vào Material
                    var modelAnglePattern = FillPatternElement.GetFillPatternElementByName(doc, FillPatternTarget.Model, "ANGLE");
                    if (modelAnglePattern == null)
                    {
                        double spacingFt = 250.0 * MM_TO_FT; // Gạch 250x250
                        var fp = new FillPattern("ANGLE", FillPatternTarget.Model, FillPatternHostOrientation.ToHost, Math.PI / 4.0, spacingFt, spacingFt);
                        modelAnglePattern = FillPatternElement.Create(doc, fp);
                    }

                    // Gán vào Material WC (ID 107066) nếu có
                    var matWc = doc.GetElement(new ElementId(107066L)) as Material
                        ?? new FilteredElementCollector(doc).OfClass(typeof(Material)).Cast<Material>().FirstOrDefault(m => m.Name.Contains("WC"));
                    if (matWc != null && modelAnglePattern != null)
                    {
                        matWc.SurfaceForegroundPatternId = modelAnglePattern.Id;
                        matWc.SurfaceForegroundPatternColor = new Color(128, 128, 128);
                    }
                }
                else
                {
                    string ftName = $"Sàn BTCT {thicknessMm:0}mm";
                    targetFloorType = new FilteredElementCollector(doc)
                        .OfClass(typeof(FloorType))
                        .Cast<FloorType>()
                        .FirstOrDefault(f => f.Name.Equals(ftName, StringComparison.OrdinalIgnoreCase));

                    if (targetFloorType == null)
                    {
                        var baseFt = doc.GetElement(new ElementId(2381543L)) as FloorType // Sàn BTCT 100mm
                            ?? doc.GetElement(new ElementId(107059L)) as FloorType // SÀN BÊ TÔNG
                            ?? new FilteredElementCollector(doc).OfClass(typeof(FloorType)).Cast<FloorType>().First();

                        targetFloorType = (FloorType)baseFt.Duplicate(ftName);

                        var cs = targetFloorType.GetCompoundStructure();
                        int structIdx = cs.StructuralMaterialIndex;
                        if (structIdx < 0) structIdx = 0;
                        cs.SetLayerWidth(structIdx, thicknessMm * MM_TO_FT);
                        targetFloorType.SetCompoundStructure(cs);
                    }
                }

                txType.Commit();
            }

            if (targetFloorType == null)
            {
                return new { success = false, error = "Không thể khởi tạo loại sàn (FloorType) phù hợp!" };
            }

            // 5. Tạo danh sách CurveLoop từ tọa độ điểm
            var curveLoops = new List<CurveLoop>();
            foreach (var pts in loopsData)
            {
                var loop = new CurveLoop();
                for (int i = 0; i < pts.Count; i++)
                {
                    int j = (i + 1) % pts.Count;
                    var p0 = new XYZ(pts[i].x * MM_TO_FT, pts[i].y * MM_TO_FT, 0.0);
                    var p1 = new XYZ(pts[j].x * MM_TO_FT, pts[j].y * MM_TO_FT, 0.0);

                    // Bỏ qua đoạn thẳng quá ngắn (< 1mm)
                    if (p0.DistanceTo(p1) > (1.0 * MM_TO_FT))
                    {
                        loop.Append(Line.CreateBound(p0, p1));
                    }
                }
                if (loop.IsOpen())
                {
                    // Tự động đóng loop nếu hở
                    var pStart = loop.First().GetEndPoint(0);
                    var pEnd = loop.Last().GetEndPoint(1);
                    if (pStart.DistanceTo(pEnd) > 1.0 * MM_TO_FT)
                    {
                        loop.Append(Line.CreateBound(pEnd, pStart));
                    }
                }
                curveLoops.Add(loop);
            }

            // 6. Thực thi: Thay thế (xóa sàn cũ) hoặc Tạo mới sàn
            Floor? newFloor = null;
            bool isReplacing = (selectedFloor != null);
            long replacedId = selectedFloor?.Id.Value ?? -1;

            using (var tx = new Transaction(doc, isReplacing ? $"Thay thế Sàn ID {replacedId} từ CAD" : $"Tạo Sàn {targetFloorType.Name} từ CAD"))
            {
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new SlabWarningSwallower());
                tx.SetFailureHandlingOptions(opt);
                tx.Start();

                // Nếu đang chọn sàn: Xóa sàn cũ
                if (isReplacing && selectedFloor != null)
                {
                    try
                    {
                        doc.Delete(selectedFloor.Id);
                    }
                    catch {}
                }

                // Tạo sàn mới
                try
                {
                    newFloor = Floor.Create(doc, curveLoops, targetFloorType.Id, targetLevelId);
                }
                catch (Exception ex)
                {
                    if (curveLoops.Count > 1)
                    {
                        try
                        {
                            newFloor = Floor.Create(doc, new List<CurveLoop> { curveLoops[0] }, targetFloorType.Id, targetLevelId);
                        }
                        catch (Exception ex2)
                        {
                            tx.RollBack();
                            return new { success = false, error = $"Lỗi tạo sàn Revit từ CurveLoop: {ex2.Message}" };
                        }
                    }
                    else
                    {
                        tx.RollBack();
                        return new { success = false, error = $"Lỗi tạo sàn Revit từ CurveLoop: {ex.Message}" };
                    }
                }

                // Gán cao độ Offset
                if (newFloor != null)
                {
                    var pOffset = newFloor.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM);
                    if (pOffset != null && !pOffset.IsReadOnly)
                    {
                        pOffset.Set(offsetMm * MM_TO_FT);
                    }
                }

                doc.Regenerate();
                tx.Commit();
            }

            if (newFloor == null)
            {
                return new { success = false, error = "Lỗi khi tạo sàn trong Revit từ CurveLoop AutoCAD!" };
            }

            // Tự động chọn (Select) sàn mới vừa tạo trên màn hình Revit
            try
            {
                uidoc.Selection.SetElementIds(new List<ElementId> { newFloor.Id });
            }
            catch {}

            double areaSqm = 0.0;
            var pArea = newFloor.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED);
            if (pArea != null)
            {
                areaSqm = Math.Round(pArea.AsDouble() * SQFT_TO_SQM, 2);
            }

            return new
            {
                success = true,
                isReplacing,
                replacedFloorId = replacedId,
                floorId = newFloor.Id.Value,
                floorTypeName = targetFloorType.Name,
                levelName = targetLevelName,
                levelId = targetLevelId.Value,
                thicknessMm,
                offsetMm,
                areaSqm,
                loopCount = curveLoops.Count,
                message = isReplacing
                    ? $"ĐÃ THAY THẾ sàn ID {replacedId} thành sàn mới ID {newFloor.Id.Value} ({targetFloorType.Name}) tại {targetLevelName} (Diện tích: {areaSqm} m²)."
                    : $"ĐÃ TẠO MỚI sàn ID {newFloor.Id.Value} ({targetFloorType.Name}) tại {targetLevelName} (Diện tích: {areaSqm} m²)."
            };
        }

        public static object DeleteElements(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { success = false, error = "Không có tài liệu Revit nào đang mở!" };

            var targetArgs = args.ValueKind == JsonValueKind.Object && args.TryGetProperty("args", out var innerArgs) && innerArgs.ValueKind == JsonValueKind.Object ? innerArgs : args;

            var idsToDelete = new List<ElementId>();
            if (targetArgs.TryGetProperty("ids", out var pIds) && pIds.ValueKind == JsonValueKind.Array)
            {
                for (int i = 0; i < pIds.GetArrayLength(); i++)
                {
                    idsToDelete.Add(new ElementId(pIds[i].GetInt64()));
                }
            }

            int deletedCount = 0;
            using (var tx = new Transaction(doc, "Delete Elements"))
            {
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new SlabWarningSwallower());
                tx.SetFailureHandlingOptions(opt);
                tx.Start();

                foreach (var id in idsToDelete)
                {
                    try
                    {
                        var el = doc.GetElement(id);
                        if (el != null)
                        {
                            doc.Delete(id);
                            deletedCount++;
                        }
                    }
                    catch {}
                }

                tx.Commit();
            }

            return new { success = true, deletedCount, message = $"Đã xóa {deletedCount} đối tượng." };
        }
    }
}
