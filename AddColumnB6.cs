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
    public class AddColumnWarningSwallower : IFailuresPreprocessor
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

    public static class AddColumnB6
    {
        private const double M2FT = 3.2808398950131235;
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active Revit doc" };

            // 1. Get Levels
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .ToList();

            var lvlTang1 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));
            var lvlTang2 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 2", StringComparison.OrdinalIgnoreCase));
            if (lvlTang1 == null) return new { error = "Level TẦNG 1 not found" };
            if (lvlTang2 == null) return new { error = "Level TẦNG 2 not found" };

            // 2. Get Symbol COT250X400
            var allStructSymbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>()
                .ToList();

            FamilySymbol sym250 = allStructSymbols.FirstOrDefault(s => s.Name == "COT250X400");
            if (sym250 == null)
            {
                FamilySymbol baseSym = allStructSymbols.FirstOrDefault(s => s.FamilyName.Contains("Concrete", StringComparison.OrdinalIgnoreCase))
                                    ?? allStructSymbols.FirstOrDefault();
                if (baseSym == null) return new { error = "No concrete column family found" };

                using (var txSym = new Transaction(doc, "Create COT250X400"))
                {
                    txSym.Start();
                    sym250 = baseSym.Duplicate("COT250X400") as FamilySymbol;
                    sym250.LookupParameter("b")?.Set(0.250 * M2FT);
                    sym250.LookupParameter("h")?.Set(0.400 * M2FT);
                    if (!sym250.IsActive) sym250.Activate();
                    txSym.Commit();
                }
            }
            else if (!sym250.IsActive)
            {
                using (var txAct = new Transaction(doc, "Activate COT250X400"))
                {
                    txAct.Start();
                    sym250.Activate();
                    txAct.Commit();
                }
            }

            // 3. Place column at B-6 (X = 18.850m, Y = 5.300m)
            FamilyInstance colB6 = null;
            double xB6 = 18.850;
            double yB6 = 5.300;

            using (var txCreate = new Transaction(doc, "Add Column B-6 (COT250X400)"))
            {
                txCreate.Start();
                var opt = txCreate.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new AddColumnWarningSwallower());
                txCreate.SetFailureHandlingOptions(opt);

                var pt = new XYZ(xB6 * M2FT, yB6 * M2FT, lvlTang1.Elevation);
                colB6 = doc.Create.NewFamilyInstance(pt, sym250, lvlTang1, StructuralType.Column);

                if (colB6 != null)
                {
                    colB6.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM)?.Set(lvlTang1.Id);
                    colB6.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM)?.Set(lvlTang2.Id);

                    var pBaseOffset = colB6.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_OFFSET_PARAM) ?? colB6.LookupParameter("Base Offset");
                    if (pBaseOffset != null && !pBaseOffset.IsReadOnly) pBaseOffset.Set(0.0);

                    var pTopOffset = colB6.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM) ?? colB6.LookupParameter("Top Offset");
                    if (pTopOffset != null && !pTopOffset.IsReadOnly) pTopOffset.Set(0.0);
                }

                doc.Regenerate();
                txCreate.Commit();
            }

            // 4. Select the new column B-6 and B-5 for focus/highlight
            var selIds = new List<ElementId>();
            if (colB6 != null) selIds.Add(colB6.Id);

            // Find B-5 column as well
            var allCols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .ToList();

            var colB5 = allCols.FirstOrDefault(c =>
            {
                if (c.Location is LocationPoint lp)
                {
                    double cx = lp.Point.X * FT2M;
                    double cy = lp.Point.Y * FT2M;
                    return Math.Abs(cx - 15.250) < 0.05 && Math.Abs(cy - 5.300) < 0.05;
                }
                return false;
            });
            if (colB5 != null) selIds.Add(colB5.Id);

            try
            {
                uidoc.Selection.SetElementIds(selIds);
            }
            catch { }

            // 5. Focus view on B-5 to B-7 zone
            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == uidoc.ActiveView.Id);
            if (uiview != null)
            {
                XYZ pMin = new XYZ(13.0 * M2FT, 3.5 * M2FT, 0.0);
                XYZ pMax = new XYZ(24.5 * M2FT, 7.5 * M2FT, 0.0);
                uiview.ZoomAndCenterRectangle(pMin, pMax);
            }

            // 6. Export close-up verification image
            string outImgPath = "C:\\\\Users\\\\nguyenbuu.DESKTOP-TOEFTR1\\\\.gemini\\\\antigravity\\\\brain\\\\16005848-1987-4ccc-a037-b18d9e878697\\\\revit_column_b6_result.png";
            if (File.Exists(outImgPath)) { try { File.Delete(outImgPath); } catch { } }

            try
            {
                var expOpt = new ImageExportOptions
                {
                    FilePath = outImgPath,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_300,
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 2500
                };
                doc.ExportImage(expOpt);
            }
            catch { }

            int totalStructCols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsNotElementType()
                .GetElementCount();

            return new
            {
                success = true,
                column = new
                {
                    id = colB6?.Id.Value,
                    grid = "B-6",
                    symbol = sym250.Name,
                    x = xB6,
                    y = yB6,
                    widthMm = 250,
                    depthMm = 400,
                    baseLevel = lvlTang1.Name,
                    topLevel = lvlTang2.Name
                },
                totalStructuralColumns = totalStructCols,
                exportImage = outImgPath
            };
        }
    }
}
