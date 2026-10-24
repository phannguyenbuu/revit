using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Structure;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class GenericWarningSwallower : IFailuresPreprocessor
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

    public static class SplitColumnsAndChangeText
    {
        private const double M2FT = 3.2808398950131235;
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active doc" };

            var result = new Dictionary<string, object>();

            // =========================================================================
            // PART 1: CHUYỂN TẤT CẢ TEXT VỀ STYLE "2.5mm Arial"
            // =========================================================================
            var textTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(TextNoteType))
                .Cast<TextNoteType>()
                .ToList();

            var targetTextType = textTypes.FirstOrDefault(t => t.Name.Equals("2.5mm Arial", StringComparison.OrdinalIgnoreCase))
                                 ?? textTypes.FirstOrDefault(t => t.Id.Value == 361);

            if (targetTextType == null)
            {
                result["textChangeError"] = "Target TextNoteType '2.5mm Arial' not found!";
            }
            else
            {
                var allNotes = new FilteredElementCollector(doc)
                    .OfClass(typeof(TextNote))
                    .WhereElementIsNotElementType()
                    .Cast<TextNote>()
                    .ToList();

                int textConverted = 0;
                int textAlreadyTarget = 0;
                var textFailures = new List<string>();

                using (var txText = new Transaction(doc, "Change All Text To 2.5mm Arial"))
                {
                    var opt = txText.GetFailureHandlingOptions();
                    opt.SetFailuresPreprocessor(new GenericWarningSwallower());
                    txText.SetFailureHandlingOptions(opt);

                    txText.Start();
                    foreach (var note in allNotes)
                    {
                        if (note.GetTypeId() == targetTextType.Id)
                        {
                            textAlreadyTarget++;
                            continue;
                        }

                        try
                        {
                            note.ChangeTypeId(targetTextType.Id);
                            textConverted++;
                        }
                        catch (Exception ex)
                        {
                            textFailures.Add($"Note {note.Id.Value}: {ex.Message}");
                        }
                    }
                    txText.Commit();
                }

                result["textSummary"] = new
                {
                    targetTypeId = targetTextType.Id.Value,
                    targetTypeName = targetTextType.Name,
                    totalTextNotes = allNotes.Count,
                    converted = textConverted,
                    alreadyTarget = textAlreadyTarget,
                    failures = textFailures
                };
            }

            // =========================================================================
            // PART 2: NGẮT CỘT THEO TỪNG TẦNG (LEVEL-BY-LEVEL - PHƯƠNG ÁN 1)
            // =========================================================================
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .OrderBy(l => l.Elevation)
                .ToList();

            Level lvlTang1 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));
            Level lvlTang2 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 2", StringComparison.OrdinalIgnoreCase));
            Level lvlTang3 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 3", StringComparison.OrdinalIgnoreCase));
            Level lvlTang4 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 4", StringComparison.OrdinalIgnoreCase));
            Level lvlApMai = levels.FirstOrDefault(l => l.Name.Contains("ÁP MÁI", StringComparison.OrdinalIgnoreCase)) ?? lvlTang4;
            Level lvlTum = levels.FirstOrDefault(l => l.Name.Contains("TUM", StringComparison.OrdinalIgnoreCase));
            Level lvlMai = levels.FirstOrDefault(l => l.Name.Contains("MÁI", StringComparison.OrdinalIgnoreCase) && !l.Name.Contains("ÁP MÁI", StringComparison.OrdinalIgnoreCase));

            if (lvlTang1 == null || lvlTang2 == null || lvlTang3 == null || lvlTang4 == null || lvlTum == null)
            {
                result["columnError"] = "Could not identify standard building levels";
                return result;
            }

            // Collect all existing structural columns
            var existingCols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .ToList();

            int initialColumnCount = existingCols.Count;

            // Cache data of all existing columns
            var colDataList = new List<(
                FamilyInstance inst,
                FamilySymbol sym,
                XYZ pt,
                double rotation,
                Level originalTopLvl,
                double originalTopOffsetFt,
                double originalTopElevFt
            )>();

            foreach (var c in existingCols)
            {
                var lp = c.Location as LocationPoint;
                if (lp == null) continue;

                var pTop = c.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM);
                var topId = pTop != null ? pTop.AsElementId() : ElementId.InvalidElementId;
                var topLvl = topId != ElementId.InvalidElementId ? doc.GetElement(topId) as Level : null;

                var pTopOff = c.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM);
                double topOffFt = pTopOff != null ? pTopOff.AsDouble() : 0.0;
                double topElevFt = (topLvl?.Elevation ?? 0.0) + topOffFt;

                colDataList.Add((c, c.Symbol, lp.Point, lp.Rotation, topLvl, topOffFt, topElevFt));
            }

            int countTang1to2 = 0;
            int countTang2to3 = 0;
            int countTang3to4 = 0;
            int countTang4toTumOrApMai = 0;
            int countTumToMai = 0;

            var newColIds = new List<ElementId>();

            using (var txCol = new Transaction(doc, "Split Columns Floor by Floor (Option 1)"))
            {
                var opt = txCol.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new GenericWarningSwallower());
                txCol.SetFailureHandlingOptions(opt);

                txCol.Start();

                foreach (var data in colDataList)
                {
                    var col1 = data.inst;
                    var sym = data.sym;
                    var pt = data.pt;
                    double rot = data.rotation;
                    var origTopLvl = data.originalTopLvl;
                    double origTopOffFt = data.originalTopOffsetFt;
                    double origTopElevM = data.originalTopElevFt * FT2M;

                    // 1. Cập nhật cột hiện tại thành Segment 1: Tầng 1 -> Tầng 2
                    var pBase1 = col1.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM);
                    var pTop1 = col1.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM);
                    var pBaseOff1 = col1.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_OFFSET_PARAM);
                    var pTopOff1 = col1.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM);

                    if (pTop1 != null && !pTop1.IsReadOnly) pTop1.Set(lvlTang2.Id);
                    if (pBase1 != null && !pBase1.IsReadOnly) pBase1.Set(lvlTang1.Id);
                    if (pBaseOff1 != null && !pBaseOff1.IsReadOnly) pBaseOff1.Set(0.0);
                    if (pTopOff1 != null && !pTopOff1.IsReadOnly) pTopOff1.Set(0.0);
                    countTang1to2++;

                    // Helper function to create a new column segment
                    FamilyInstance CreateColumnSegment(Level baseLvl, Level topLvl, double topOffsetM)
                    {
                        var newPt = new XYZ(pt.X, pt.Y, baseLvl.Elevation);
                        var newCol = doc.Create.NewFamilyInstance(newPt, sym, baseLvl, StructuralType.Column);

                        var pB = newCol.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM);
                        var pT = newCol.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM);
                        var pBOff = newCol.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_OFFSET_PARAM);
                        var pTOff = newCol.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM);

                        if (pT != null && !pT.IsReadOnly) pT.Set(topLvl.Id);
                        if (pB != null && !pB.IsReadOnly) pB.Set(baseLvl.Id);
                        if (pBOff != null && !pBOff.IsReadOnly) pBOff.Set(0.0);
                        if (pTOff != null && !pTOff.IsReadOnly) pTOff.Set(topOffsetM * M2FT);

                        if (Math.Abs(rot) > 1e-5)
                        {
                            var axis = Line.CreateBound(newPt, new XYZ(newPt.X, newPt.Y, newPt.Z + 10.0));
                            ElementTransformUtils.RotateElement(doc, newCol.Id, axis, rot);
                        }

                        newColIds.Add(newCol.Id);
                        return newCol;
                    }

                    // 2. Segment 2: Tầng 2 -> Tầng 3
                    CreateColumnSegment(lvlTang2, lvlTang3, 0.0);
                    countTang2to3++;

                    // 3. Segment 3: Tầng 3 -> Tầng 4
                    CreateColumnSegment(lvlTang3, lvlTang4, 0.0);
                    countTang3to4++;

                    // 4. Segment 4: Tầng 4 -> Tầng Tum (hoặc Áp Mái)
                    // Kiểm tra xem cột này ban đầu có vượt qua Tầng 4 (10.8m) hay không
                    if (origTopElevM > 10.85)
                    {
                        // Kiểm tra nếu là cột Áp Mái với offset 1.5m
                        if (origTopLvl != null && origTopLvl.Name.Contains("ÁP MÁI", StringComparison.OrdinalIgnoreCase))
                        {
                            CreateColumnSegment(lvlTang4, lvlApMai, origTopOffFt * FT2M);
                            countTang4toTumOrApMai++;
                        }
                        else
                        {
                            CreateColumnSegment(lvlTang4, lvlTum, 0.0);
                            countTang4toTumOrApMai++;
                        }
                    }

                    // 5. Segment 5: Tầng Tum -> Mái (cho 2 cột thang bộ lên tới Mái 17.2m)
                    if (origTopElevM > 14.5 && lvlMai != null)
                    {
                        CreateColumnSegment(lvlTum, lvlMai, 0.0);
                        countTumToMai++;
                    }
                }

                doc.Regenerate();
                txCol.Commit();
            }

            int finalColumnCount = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsNotElementType()
                .GetElementCount();

            result["columnSummary"] = new
            {
                initialCount = initialColumnCount,
                finalCount = finalColumnCount,
                tang1to2 = countTang1to2,
                tang2to3 = countTang2to3,
                tang3to4 = countTang3to4,
                tang4toTumOrApMai = countTang4toTumOrApMai,
                tumToMai = countTumToMai,
                totalSegmentsCreated = countTang2to3 + countTang3to4 + countTang4toTumOrApMai + countTumToMai
            };

            // =========================================================================
            // PART 3: XUẤT ẢNH NGHIỆM THU
            // =========================================================================
            try
            {
                string out3dImg = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_columns_split_floor_by_floor_3d.png";
                if (File.Exists(out3dImg)) { try { File.Delete(out3dImg); } catch { } }

                var expOpt = new ImageExportOptions
                {
                    FilePath = out3dImg,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_300,
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 3000
                };
                doc.ExportImage(expOpt);
                result["exportedImage"] = out3dImg;
            }
            catch (Exception ex)
            {
                result["exportError"] = ex.Message;
            }

            return result;
        }
    }
}
