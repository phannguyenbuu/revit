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
    public class ColumnOption1WarningSwallower : IFailuresPreprocessor
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

    public static class ApplyOptimalColumnSectionsOption1
    {
        private const double M2FT = 3.2808398950131235;
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active doc" };

            // 1. Get or create required Column Symbols in M_Concrete-Rectangular-Column
            var allStructSymbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>()
                .ToList();

            var baseSym = allStructSymbols.FirstOrDefault(s => s.FamilyName.Contains("Concrete", StringComparison.OrdinalIgnoreCase))
                          ?? allStructSymbols.FirstOrDefault();
            if (baseSym == null) return new { error = "No concrete column family found" };

            var symbolDefs = new (string name, double bMm, double hMm)[]
            {
                ("COT250X400", 250, 400),
                ("COT250X350", 250, 350),
                ("COT220X300", 220, 300),
                ("COT220X250", 220, 250),
                ("COT200X250", 200, 250),
                ("COT200X200", 200, 200)
            };

            var symbolDict = new Dictionary<string, FamilySymbol>(StringComparer.OrdinalIgnoreCase);

            using (var txSym = new Transaction(doc, "Create Column Symbols for Option 1"))
            {
                txSym.Start();
                foreach (var def in symbolDefs)
                {
                    var existing = allStructSymbols.FirstOrDefault(s => s.Name.Equals(def.name, StringComparison.OrdinalIgnoreCase));
                    if (existing == null)
                    {
                        existing = baseSym.Duplicate(def.name) as FamilySymbol;
                        if (existing != null)
                        {
                            allStructSymbols.Add(existing);
                        }
                    }
                    if (existing != null)
                    {
                        var pB = existing.LookupParameter("b");
                        var pH = existing.LookupParameter("h");
                        if (pB != null && !pB.IsReadOnly) pB.Set(def.bMm / 1000.0 * M2FT);
                        if (pH != null && !pH.IsReadOnly) pH.Set(def.hMm / 1000.0 * M2FT);

                        if (!existing.IsActive) existing.Activate();
                        symbolDict[def.name] = existing;
                    }
                }
                txSym.Commit();
            }

            // 2. Collect all structural columns
            var cols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .ToList();

            int updatedCount = 0;
            var summaryByType = new Dictionary<string, int>();
            var summaryByLevelAndType = new Dictionary<string, Dictionary<string, int>>();

            using (var txCol = new Transaction(doc, "Apply Optimal Column Sections (Option 1)"))
            {
                var opt = txCol.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new ColumnOption1WarningSwallower());
                txCol.SetFailureHandlingOptions(opt);

                txCol.Start();

                foreach (var col in cols)
                {
                    var lp = col.Location as LocationPoint;
                    if (lp == null) continue;

                    var pBase = col.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM);
                    var baseLvl = pBase != null && pBase.AsElementId() != ElementId.InvalidElementId
                        ? doc.GetElement(pBase.AsElementId()) as Level : null;

                    string lvlName = baseLvl?.Name ?? "Unknown";
                    double curX = lp.Point.X * FT2M * 1000.0; // mm
                    double curY = lp.Point.Y * FT2M * 1000.0; // mm

                    // Determine floor
                    int story = 1;
                    if (lvlName.Contains("TẦNG 2", StringComparison.OrdinalIgnoreCase)) story = 2;
                    else if (lvlName.Contains("TẦNG 3", StringComparison.OrdinalIgnoreCase)) story = 3;
                    else if (lvlName.Contains("TẦNG 4", StringComparison.OrdinalIgnoreCase)) story = 4;
                    else if (lvlName.Contains("TUM", StringComparison.OrdinalIgnoreCase)) story = 5;
                    else if (lvlName.Contains("ÁP MÁI", StringComparison.OrdinalIgnoreCase)) story = 4;

                    // Determine column group & target type
                    string targetSymName = "COT250X400";
                    double newDepthMm = 400;
                    double targetY = curY;

                    // A. Cột buồng thang (Trục E: Y >= 14000)
                    if (curY >= 14000)
                    {
                        targetSymName = "COT200X200";
                        newDepthMm = 200;
                        targetY = 14900;
                    }
                    // B. Cột góc (X <= 1000 hoặc X >= 36500) VÀ (Trục A: Y <= 500 hoặc Trục D: Y >= 12500)
                    else if ((curX <= 1000 || curX >= 36500) && (curY <= 500 || (curY >= 12500 && curY < 14000)))
                    {
                        if (story == 1)
                        {
                            targetSymName = "COT220X250";
                            newDepthMm = 250;
                        }
                        else
                        {
                            targetSymName = "COT200X200";
                            newDepthMm = 200;
                        }

                        // Align flush
                        if (curY <= 500) targetY = -100.0 + newDepthMm / 2.0; // Trục A
                        else targetY = 13300.0 - newDepthMm / 2.0;             // Trục D
                    }
                    // C. Cột biên Trục A (Y <= 500)
                    else if (curY <= 500)
                    {
                        // Check if Trục 6-A (X ~ 18850)
                        if (Math.Abs(curX - 18850) < 500)
                        {
                            targetSymName = "COT200X200";
                            newDepthMm = 200;
                            targetY = 0.0;
                        }
                        else
                        {
                            if (story == 1) { targetSymName = "COT250X350"; newDepthMm = 350; }
                            else if (story == 2) { targetSymName = "COT220X300"; newDepthMm = 300; }
                            else if (story == 3) { targetSymName = "COT200X250"; newDepthMm = 250; }
                            else { targetSymName = "COT200X200"; newDepthMm = 200; }

                            targetY = -100.0 + newDepthMm / 2.0; // Mép ngoài phẳng Y = -100
                        }
                    }
                    // D. Cột biên Trục D (Y ~ 13100)
                    else if (curY >= 12500 && curY < 14000)
                    {
                        if (story == 1) { targetSymName = "COT250X350"; newDepthMm = 350; }
                        else if (story == 2) { targetSymName = "COT220X300"; newDepthMm = 300; }
                        else if (story == 3) { targetSymName = "COT200X250"; newDepthMm = 250; }
                        else { targetSymName = "COT200X200"; newDepthMm = 200; }

                        targetY = 13300.0 - newDepthMm / 2.0; // Mép ngoài phẳng Y = +13300
                    }
                    // E. Cột giữa Trục B (Y ~ 5300)
                    else if (curY >= 5000 && curY <= 5700)
                    {
                        if (story == 1) { targetSymName = "COT250X400"; newDepthMm = 400; }
                        else if (story == 2) { targetSymName = "COT250X350"; newDepthMm = 350; }
                        else if (story == 3) { targetSymName = "COT220X300"; newDepthMm = 300; }
                        else if (story == 4) { targetSymName = "COT200X250"; newDepthMm = 250; }
                        else { targetSymName = "COT200X200"; newDepthMm = 200; }

                        targetY = 5500.0 - newDepthMm / 2.0; // Mép hành lang phẳng Y = +5500
                    }
                    // F. Cột giữa Trục C (Y ~ 7900)
                    else if (curY >= 7500 && curY <= 8200)
                    {
                        if (story == 1) { targetSymName = "COT250X400"; newDepthMm = 400; }
                        else if (story == 2) { targetSymName = "COT250X350"; newDepthMm = 350; }
                        else if (story == 3) { targetSymName = "COT220X300"; newDepthMm = 300; }
                        else if (story == 4) { targetSymName = "COT200X250"; newDepthMm = 250; }
                        else { targetSymName = "COT200X200"; newDepthMm = 200; }

                        targetY = 7700.0 + newDepthMm / 2.0; // Mép hành lang phẳng Y = +7700
                    }

                    // Apply Symbol
                    if (symbolDict.TryGetValue(targetSymName, out var targetSym) && targetSym != null)
                    {
                        if (col.GetTypeId() != targetSym.Id)
                        {
                            col.ChangeTypeId(targetSym.Id);
                        }
                    }

                    // Apply Location Shift along Y for flush faces
                    double dYFt = (targetY - curY) / 1000.0 * M2FT;
                    if (Math.Abs(dYFt) > 1e-4)
                    {
                        ElementTransformUtils.MoveElement(doc, col.Id, new XYZ(0, dYFt, 0));
                    }

                    updatedCount++;
                    summaryByType[targetSymName] = summaryByType.GetValueOrDefault(targetSymName, 0) + 1;

                    if (!summaryByLevelAndType.ContainsKey(lvlName))
                    {
                        summaryByLevelAndType[lvlName] = new Dictionary<string, int>();
                    }
                    summaryByLevelAndType[lvlName][targetSymName] = summaryByLevelAndType[lvlName].GetValueOrDefault(targetSymName, 0) + 1;
                }

                doc.Regenerate();
                txCol.Commit();
            }

            // Export verification image
            string folder = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            string outImg = Path.Combine(folder, "revit_columns_option1_updated_3d.png");
            if (File.Exists(outImg)) { try { File.Delete(outImg); } catch { } }

            try
            {
                var view3d = new FilteredElementCollector(doc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate && v.Name.Equals("{3D}", StringComparison.OrdinalIgnoreCase))
                    ?? new FilteredElementCollector(doc).OfClass(typeof(View3D)).Cast<View3D>().FirstOrDefault(v => !v.IsTemplate);

                if (view3d != null)
                {
                    uidoc.ActiveView = view3d;
                    var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view3d.Id);
                    uiview?.ZoomToFit();

                    var expOpts = new ImageExportOptions
                    {
                        FilePath = outImg,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.PNG,
                        ImageResolution = ImageResolution.DPI_300,
                        ExportRange = ExportRange.VisibleRegionOfCurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 3000
                    };
                    doc.ExportImage(expOpts);
                }
            }
            catch { }

            return new
            {
                success = true,
                totalColumnsUpdated = updatedCount,
                summaryByType,
                summaryByLevelAndType,
                image = outImg
            };
        }
    }
}
