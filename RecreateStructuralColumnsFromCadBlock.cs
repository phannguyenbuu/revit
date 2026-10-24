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
    public class ColumnWarningSwallower : IFailuresPreprocessor
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

    public static class RecreateStructuralColumnsFromCadBlock
    {
        private const double M2FT = 3.2808398950131235;
        private const double FT2M = 0.3048;

        public struct ColDef
        {
            public double X;
            public double Y;
            public int W;
            public int D;
            public string SymbolName;

            public ColDef(double x, double y, int w, int d, string sym)
            {
                X = x;
                Y = y;
                W = w;
                D = d;
                SymbolName = sym;
            }
        }

        private static readonly ColDef[] Columns = new ColDef[]
        {
                new ColDef(18.8500, 0.0000, 200, 200, "COT200X200"),
                new ColDef(0.5500, 0.1000, 250, 400, "COT250X400"),
                new ColDef(4.3500, 0.1000, 250, 400, "COT250X400"),
                new ColDef(8.0500, 0.1000, 250, 400, "COT250X400"),
                new ColDef(11.6500, 0.1000, 250, 400, "COT250X400"),
                new ColDef(15.2500, 0.1000, 250, 400, "COT250X400"),
                new ColDef(22.4500, 0.1000, 250, 400, "COT250X400"),
                new ColDef(26.0500, 0.1000, 250, 400, "COT250X400"),
                new ColDef(29.6500, 0.1000, 250, 400, "COT250X400"),
                new ColDef(33.3500, 0.1000, 250, 400, "COT250X400"),
                new ColDef(37.1500, 0.1000, 250, 400, "COT250X400"),
                new ColDef(0.5500, 5.3000, 250, 400, "COT250X400"),
                new ColDef(4.3500, 5.3000, 250, 400, "COT250X400"),
                new ColDef(8.0500, 5.3000, 250, 400, "COT250X400"),
                new ColDef(11.6500, 5.3000, 250, 400, "COT250X400"),
                new ColDef(15.2500, 5.3000, 250, 400, "COT250X400"),
                new ColDef(22.4500, 5.3000, 250, 400, "COT250X400"),
                new ColDef(26.0500, 5.3000, 250, 400, "COT250X400"),
                new ColDef(29.6500, 5.3000, 250, 400, "COT250X400"),
                new ColDef(33.3500, 5.3000, 250, 400, "COT250X400"),
                new ColDef(37.1500, 5.3000, 250, 400, "COT250X400"),
                new ColDef(0.5500, 7.9000, 250, 400, "COT250X400"),
                new ColDef(4.3500, 7.9000, 250, 400, "COT250X400"),
                new ColDef(8.0500, 7.9000, 250, 400, "COT250X400"),
                new ColDef(11.6500, 7.9000, 250, 400, "COT250X400"),
                new ColDef(15.2500, 7.9000, 250, 400, "COT250X400"),
                new ColDef(18.8500, 7.9000, 250, 400, "COT250X400"),
                new ColDef(22.4500, 7.9000, 250, 400, "COT250X400"),
                new ColDef(26.0500, 7.9000, 250, 400, "COT250X400"),
                new ColDef(29.6500, 7.9000, 250, 400, "COT250X400"),
                new ColDef(33.3500, 7.9000, 250, 400, "COT250X400"),
                new ColDef(37.1500, 7.9000, 250, 400, "COT250X400"),
                new ColDef(0.5500, 13.1000, 250, 400, "COT250X400"),
                new ColDef(4.3500, 13.1000, 250, 400, "COT250X400"),
                new ColDef(8.0500, 13.1000, 250, 400, "COT250X400"),
                new ColDef(11.6500, 13.1000, 250, 400, "COT250X400"),
                new ColDef(15.2500, 13.1000, 250, 400, "COT250X400"),
                new ColDef(18.8500, 13.1000, 250, 400, "COT250X400"),
                new ColDef(22.4500, 13.1000, 250, 400, "COT250X400"),
                new ColDef(26.0500, 13.1000, 250, 400, "COT250X400"),
                new ColDef(29.6500, 13.1000, 250, 400, "COT250X400"),
                new ColDef(33.3500, 13.1000, 250, 400, "COT250X400"),
                new ColDef(37.1500, 13.1000, 250, 400, "COT250X400"),
                new ColDef(4.3500, 14.9000, 200, 200, "COT200X200"),
                new ColDef(8.0500, 14.9000, 200, 200, "COT200X200"),
                new ColDef(29.6500, 14.9000, 200, 200, "COT200X200"),
                new ColDef(33.3500, 14.9000, 200, 200, "COT200X200")
        };

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

            // 2. Delete ALL existing structural columns and architectural columns
            int deletedCount = 0;
            using (var txDel = new Transaction(doc, "Delete Existing Columns"))
            {
                txDel.Start();

                var existingStructCols = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_StructuralColumns)
                    .WhereElementIsNotElementType()
                    .ToElementIds();

                var existingArchCols = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Columns)
                    .WhereElementIsNotElementType()
                    .ToElementIds();

                var allColIds = existingStructCols.Concat(existingArchCols).ToList();
                deletedCount = allColIds.Count;

                if (allColIds.Count > 0)
                {
                    doc.Delete(allColIds);
                }

                txDel.Commit();
            }

            // 3. Prepare or Create FamilySymbols (COT250X400 and COT200X200)
            var allStructSymbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>()
                .ToList();

            FamilySymbol baseSym = allStructSymbols.FirstOrDefault(s => s.FamilyName.Contains("Concrete", StringComparison.OrdinalIgnoreCase))
                                ?? allStructSymbols.FirstOrDefault();

            if (baseSym == null) return new { error = "No concrete column family found" };

            var symbolDict = new Dictionary<string, FamilySymbol>(StringComparer.OrdinalIgnoreCase);

            using (var txSym = new Transaction(doc, "Create Column Symbols"))
            {
                txSym.Start();

                // Check or create COT250X400
                var sym250 = allStructSymbols.FirstOrDefault(s => s.Name == "COT250X400");
                if (sym250 == null)
                {
                    sym250 = baseSym.Duplicate("COT250X400") as FamilySymbol;
                }
                if (sym250 != null)
                {
                    var pB = sym250.LookupParameter("b");
                    var pH = sym250.LookupParameter("h");
                    if (pB != null && !pB.IsReadOnly) pB.Set(0.250 * M2FT);
                    if (pH != null && !pH.IsReadOnly) pH.Set(0.400 * M2FT);
                    if (!sym250.IsActive) sym250.Activate();
                    symbolDict["COT250X400"] = sym250;
                }

                // Check or create COT200X200
                var sym200 = allStructSymbols.FirstOrDefault(s => s.Name == "COT200X200");
                if (sym200 == null)
                {
                    sym200 = baseSym.Duplicate("COT200X200") as FamilySymbol;
                }
                if (sym200 != null)
                {
                    var pB = sym200.LookupParameter("b");
                    var pH = sym200.LookupParameter("h");
                    if (pB != null && !pB.IsReadOnly) pB.Set(0.200 * M2FT);
                    if (pH != null && !pH.IsReadOnly) pH.Set(0.200 * M2FT);
                    if (!sym200.IsActive) sym200.Activate();
                    symbolDict["COT200X200"] = sym200;
                }

                txSym.Commit();
            }

            // 4. Place each of the 47 columns
            var createdColIds = new List<ElementId>();
            var createdColsInfo = new List<object>();

            using (var txCreate = new Transaction(doc, "Place 47 Structural Columns from CAD Block"))
            {
                txCreate.Start();
                var opt = txCreate.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new ColumnWarningSwallower());
                txCreate.SetFailureHandlingOptions(opt);

                foreach (var c in Columns)
                {
                    if (!symbolDict.TryGetValue(c.SymbolName, out var sym) || sym == null)
                    {
                        continue;
                    }

                    var pt = new XYZ(c.X * M2FT, c.Y * M2FT, lvlTang1.Elevation);
                    FamilyInstance colInst = doc.Create.NewFamilyInstance(pt, sym, lvlTang1, StructuralType.Column);

                    if (colInst != null)
                    {
                        // Set Base Level and Top Level
                        var pBase = colInst.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM);
                        if (pBase != null && !pBase.IsReadOnly) pBase.Set(lvlTang1.Id);

                        var pTop = colInst.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM);
                        if (pTop != null && !pTop.IsReadOnly) pTop.Set(lvlTang2.Id);

                        var pBaseOffset = colInst.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_OFFSET_PARAM) ?? colInst.LookupParameter("Base Offset");
                        if (pBaseOffset != null && !pBaseOffset.IsReadOnly) pBaseOffset.Set(0.0);

                        var pTopOffset = colInst.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM) ?? colInst.LookupParameter("Top Offset");
                        if (pTopOffset != null && !pTopOffset.IsReadOnly) pTopOffset.Set(0.0);

                        createdColIds.Add(colInst.Id);
                        createdColsInfo.Add(new
                        {
                            id = colInst.Id.Value,
                            x = c.X,
                            y = c.Y,
                            w = c.W,
                            d = c.D,
                            type = c.SymbolName
                        });
                    }
                }

                doc.Regenerate();
                txCreate.Commit();
            }

            // 5. Select created columns for highlight
            try
            {
                uidoc.Selection.SetElementIds(createdColIds);
            }
            catch { }

            // 6. Focus view on whole floor plan
            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == uidoc.ActiveView.Id);
            if (uiview != null)
            {
                XYZ pMin = new XYZ(-2.0 * M2FT, -2.0 * M2FT, 0.0);
                XYZ pMax = new XYZ(40.0 * M2FT, 17.0 * M2FT, 0.0);
                uiview.ZoomAndCenterRectangle(pMin, pMax);
            }

            // 7. Export full floor plan verification image
            string outImgPath = "C:\\Users\\nguyenbuu.DESKTOP-TOEFTR1\\.gemini\\antigravity\\brain\\16005848-1987-4ccc-a037-b18d9e878697\\revit_columns_all_result.png";
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
                    PixelSize = 3000
                };
                doc.ExportImage(expOpt);
            }
            catch { }

            return new
            {
                success = true,
                deletedExistingColumns = deletedCount,
                createdColumnsCount = createdColIds.Count,
                columns250x400 = Columns.Count(c => c.SymbolName == "COT250X400"),
                columns200x200 = Columns.Count(c => c.SymbolName == "COT200X200"),
                exportImage = outImgPath
            };
        }
    }
}
