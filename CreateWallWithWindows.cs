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
    public class WindowWarningSwallower : IFailuresPreprocessor
    {
        public FailureProcessingResult PreprocessFailures(FailuresAccessor failuresAccessor)
        {
            var failureMessages = failuresAccessor.GetFailureMessages();
            foreach (var msg in failureMessages)
            {
                if (msg.GetSeverity() == FailureSeverity.Warning)
                {
                    failuresAccessor.DeleteWarning(msg);
                }
            }
            return FailureProcessingResult.Continue;
        }
    }

    public static class CreateWallWithWindows
    {
        private const double M2FT = 3.2808398950131235;
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active doc" };

            // 1. Get 200mm wall type
            var wallType200 = new FilteredElementCollector(doc)
                .OfClass(typeof(WallType))
                .Cast<WallType>()
                .FirstOrDefault(w => w.Name == "gach200_xay moi" || w.Name == "gach200" || w.Name == "Tường 200");

            if (wallType200 == null)
                return new { error = "Wall type gach200_xay moi not found" };

            // 2. Levels
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .ToList();

            var lvlTang1 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));
            var lvlTang2 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 2", StringComparison.OrdinalIgnoreCase));
            if (lvlTang1 == null) return new { error = "Level TẦNG 1 not found" };

            // 3. Find/prepare window symbols for S1 (1500mm) and S5 (800mm)
            var allWindowSymbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Windows)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>()
                .ToList();

            // Candidate for S1:
            // Symbol with TM='S1' or width=1500mm
            FamilySymbol symS1 = allWindowSymbols.FirstOrDefault(s => s.Id.Value == 144661) // CUA SO 2 CANH NHOM KINH (TM='S1')
                              ?? allWindowSymbols.FirstOrDefault(s => s.Id.Value == 2084169) // CỬA SỔ ĐẨY 2 CÁNH MỞ ERO (W=1500mm)
                              ?? allWindowSymbols.FirstOrDefault(s => s.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)?.AsString() == "S1")
                              ?? allWindowSymbols.FirstOrDefault(s => s.FamilyName.Contains("2 CANH", StringComparison.OrdinalIgnoreCase));

            // Candidate for S5:
            // Symbol with TM='S5'
            FamilySymbol symS5 = allWindowSymbols.FirstOrDefault(s => s.Id.Value == 1462958) // ATT_Window 2 (TM='S5')
                              ?? allWindowSymbols.FirstOrDefault(s => s.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)?.AsString() == "S5")
                              ?? allWindowSymbols.FirstOrDefault(s => s.FamilyName.Contains("Window", StringComparison.OrdinalIgnoreCase));

            if (symS1 == null) return new { error = "Window symbol for S1 not found" };
            if (symS5 == null) return new { error = "Window symbol for S5 not found" };

            // Prepare custom duplicate types for exact 1500mm and 800mm width if needed
            using (var txSym = new Transaction(doc, "Prepare S1 and S5 types"))
            {
                txSym.Start();
                var swallower = new WindowWarningSwallower();
                var opt = txSym.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(swallower);
                txSym.SetFailureHandlingOptions(opt);

                // Duplicate S1 to ensure width 1500mm
                var existingDupS1 = allWindowSymbols.FirstOrDefault(s => s.Name == "S1_1500x1400");
                if (existingDupS1 == null)
                {
                    symS1 = symS1.Duplicate("S1_1500x1400") as FamilySymbol;
                    var pW = symS1.get_Parameter(BuiltInParameter.WINDOW_WIDTH);
                    if (pW != null && !pW.IsReadOnly) pW.Set(1.5 * M2FT);
                    var pTM = symS1.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK);
                    if (pTM != null && !pTM.IsReadOnly) pTM.Set("S1");
                }
                else
                {
                    symS1 = existingDupS1;
                }

                // Duplicate S5 to ensure width 800mm
                var existingDupS5 = allWindowSymbols.FirstOrDefault(s => s.Name == "S5_800x600");
                if (existingDupS5 == null)
                {
                    symS5 = symS5.Duplicate("S5_800x600") as FamilySymbol;
                    var pW = symS5.get_Parameter(BuiltInParameter.WINDOW_WIDTH);
                    if (pW != null && !pW.IsReadOnly) pW.Set(0.8 * M2FT);
                    var pH = symS5.get_Parameter(BuiltInParameter.WINDOW_HEIGHT);
                    if (pH != null && !pH.IsReadOnly) pH.Set(0.6 * M2FT);
                    var pTM = symS5.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK);
                    if (pTM != null && !pTM.IsReadOnly) pTM.Set("S5");
                }
                else
                {
                    symS5 = existingDupS5;
                }

                if (!symS1.IsActive) symS1.Activate();
                if (!symS5.IsActive) symS5.Activate();

                txSym.Commit();
            }

            // 4. Clean previous wall on Grid D if exists (Y ~ 13.200)
            using (var txClean = new Transaction(doc, "Clean Previous Wall D"))
            {
                txClean.Start();
                var swallower = new WindowWarningSwallower();
                var opt = txClean.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(swallower);
                txClean.SetFailureHandlingOptions(opt);

                var oldWalls = new FilteredElementCollector(doc)
                    .OfClass(typeof(Wall))
                    .Cast<Wall>()
                    .Where(w =>
                    {
                        var lc = w.Location as LocationCurve;
                        if (lc?.Curve is Line l)
                        {
                            var p1 = l.GetEndPoint(0);
                            var p2 = l.GetEndPoint(1);
                            double ym1 = p1.Y * FT2M;
                            double ym2 = p2.Y * FT2M;
                            return Math.Abs(ym1 - 13.200) < 0.05 && Math.Abs(ym2 - 13.200) < 0.05;
                        }
                        return false;
                    })
                    .ToList();

                foreach (var w in oldWalls)
                {
                    doc.Delete(w.Id);
                }
                txClean.Commit();
            }

            // 5. Windows definitions:
            // 5 cửa sổ S1 (width 1500mm):
            // S1 #1: X = 9.800m  (P. Y Tế 1)
            // S1 #2: X = 13.400m (P. Y Tế 2)
            // S1 #3: X = 17.050m (P. Lấy lời khai)
            // S1 #4: X = 25.038m (P. Điều tra thân thiện)
            // S1 #5: X = 28.188m (Kho tang vật)
            // 2 cửa sổ S5 (width 800mm):
            // S5 #1: X = 19.438m (P. Lưu giữ 1)
            // S5 #2: X = 23.400m (P. Lưu giữ 2)
            var windowsDef = new[]
            {
                new { tag = "S1-1", sym = symS1, x = 9.800,  sillH = 0.90 },
                new { tag = "S1-2", sym = symS1, x = 13.400, sillH = 0.90 },
                new { tag = "S1-3", sym = symS1, x = 17.050, sillH = 0.90 },
                new { tag = "S5-1", sym = symS5, x = 19.438, sillH = 1.80 },
                new { tag = "S5-2", sym = symS5, x = 23.400, sillH = 1.80 },
                new { tag = "S1-4", sym = symS1, x = 25.038, sillH = 0.90 },
                new { tag = "S1-5", sym = symS1, x = 28.188, sillH = 0.90 }
            };

            Wall createdWall = null;
            var createdWindows = new List<object>();
            var selectionIds = new List<ElementId>();

            using (var tx = new Transaction(doc, "Create Wall 200 on Grid D with 7 Windows"))
            {
                tx.Start();
                var swallower = new WindowWarningSwallower();
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(swallower);
                tx.SetFailureHandlingOptions(opt);

                // Create wall along Grid D (Y = 13.200m) from X = 8.050m (Trục 3) to X = 29.650m (Trục 9)
                double yCenter = 13.200;
                var ptStart = new XYZ(8.050 * M2FT, yCenter * M2FT, 0.0);
                var ptEnd = new XYZ(29.650 * M2FT, yCenter * M2FT, 0.0);
                var line = Line.CreateBound(ptStart, ptEnd);

                double heightFt = 3.6 * M2FT;
                createdWall = Wall.Create(doc, line, wallType200.Id, lvlTang1.Id, heightFt, 0.0, false, false);
                if (lvlTang2 != null)
                {
                    var topParam = createdWall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE);
                    if (topParam != null && !topParam.IsReadOnly)
                    {
                        topParam.Set(lvlTang2.Id);
                    }
                }
                selectionIds.Add(createdWall.Id);

                // Regenerate so wall geometry and host reference exist
                doc.Regenerate();

                // Place each window
                foreach (var w in windowsDef)
                {
                    var winPt = new XYZ(w.x * M2FT, yCenter * M2FT, w.sillH * M2FT);
                    var winInst = doc.Create.NewFamilyInstance(winPt, w.sym, createdWall, lvlTang1, StructuralType.NonStructural);

                    // Set Mark parameter
                    var markParam = winInst.get_Parameter(BuiltInParameter.ALL_MODEL_MARK);
                    if (markParam != null && !markParam.IsReadOnly)
                    {
                        markParam.Set(w.tag);
                    }

                    // Set Sill Height if available
                    var sillParam = winInst.get_Parameter(BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM);
                    if (sillParam != null && !sillParam.IsReadOnly)
                    {
                        sillParam.Set(w.sillH * M2FT);
                    }

                    selectionIds.Add(winInst.Id);
                    createdWindows.Add(new
                    {
                        tag = w.tag,
                        id = winInst.Id.Value,
                        symbol = w.sym.Name,
                        family = w.sym.FamilyName,
                        x = w.x,
                        y = yCenter,
                        sillHeightM = w.sillH
                    });
                }

                tx.Commit();
            }

            // Set selection and zoom
            try
            {
                var viewTang1 = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewPlan))
                    .Cast<ViewPlan>()
                    .FirstOrDefault(v => !v.IsTemplate && v.ViewType == ViewType.FloorPlan && v.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));

                if (viewTang1 != null)
                {
                    uidoc.ActiveView = viewTang1;
                    uidoc.Selection.SetElementIds(selectionIds);

                    var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == viewTang1.Id);
                    var minPt = new XYZ(6.0 * M2FT, 9.0 * M2FT, 0.0);
                    var maxPt = new XYZ(32.0 * M2FT, 17.0 * M2FT, 0.0);
                    uiview?.ZoomAndCenterRectangle(minPt, maxPt);
                }
            }
            catch { }

            // Export high-res detail image of the new wall and windows
            string outImg = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_wall_d_windows_result.png";
            if (File.Exists(outImg)) { try { File.Delete(outImg); } catch { } }

            try
            {
                var opt = new ImageExportOptions
                {
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    FilePath = outImg,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_150,
                    PixelSize = 2560,
                    ZoomType = ZoomFitType.FitToPage
                };
                doc.ExportImage(opt);
            }
            catch { }

            return new
            {
                success = true,
                wallId = createdWall?.Id.Value,
                windowsCount = createdWindows.Count,
                windows = createdWindows,
                exportedImage = outImg
            };
        }
    }
}
