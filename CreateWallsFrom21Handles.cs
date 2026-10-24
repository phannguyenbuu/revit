using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class TwentyOneHandlesWarningSwallower : IFailuresPreprocessor
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

    public static class CreateWallsFrom21Handles
    {
        private const double M2FT = 3.2808398950131235;
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active Revit doc" };

            // 1. Get WallType gach100_xay moi
            var wallTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(WallType))
                .Cast<WallType>()
                .ToList();

            var wt100 = doc.GetElement(new ElementId(2361138)) as WallType
                     ?? wallTypes.FirstOrDefault(w => w.Name.Equals("gach100_xay moi", StringComparison.OrdinalIgnoreCase))
                     ?? wallTypes.FirstOrDefault(w => w.Name.Contains("100") && !w.Name.Contains("SENO", StringComparison.OrdinalIgnoreCase));

            if (wt100 == null) return new { error = "WallType gach100_xay moi not found" };

            // 2. Levels
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .ToList();

            var lvlTang1 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));
            var lvlTang2 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 2", StringComparison.OrdinalIgnoreCase));
            if (lvlTang1 == null) return new { error = "Level TẦNG 1 not found" };

            double heightFt = (lvlTang2 != null) ? (lvlTang2.Elevation - lvlTang1.Elevation) : (3.60 * M2FT);

            // 3. Define all clean wall segments mapped from the 21 AutoCAD handles
            var wallDefs = new List<(string feature, string name, double x1, double y1, double x2, double y2)>
            {
                // Feature 1: Staircase 1 Chase at Axis 3 (Handle 44C64C)
                ("Staircase 1 Chase (44C64C)", "Bắc", 8.050, 13.752, 8.400, 13.752),
                ("Staircase 1 Chase (44C64C)", "Đông", 8.400, 13.752, 8.400, 13.200),

                // Feature 2: Staircase 2 Chase at Axis 8 (Handle 44C2D2)
                ("Staircase 2 Chase (44C2D2)", "Bắc", 29.300, 13.752, 29.650, 13.752),
                ("Staircase 2 Chase (44C2D2)", "Tây", 29.300, 13.200, 29.300, 13.752),

                // Feature 3: Pier North 1 at X=1.90 (Handle 44C802)
                ("Pier North 1 (44C802)", "Nam",  1.750, 13.151, 2.050, 13.151),
                ("Pier North 1 (44C802)", "Đông", 2.000, 13.151, 2.000, 13.451),
                ("Pier North 1 (44C802)", "Bắc",  2.050, 13.451, 1.750, 13.451),
                ("Pier North 1 (44C802)", "Tây",  1.800, 13.451, 1.800, 13.151),

                // Feature 4: Pier North 2 at X=3.10 (Handle 44C80F)
                ("Pier North 2 (44C80F)", "Nam",  2.950, 13.151, 3.250, 13.151),
                ("Pier North 2 (44C80F)", "Đông", 3.200, 13.151, 3.200, 13.451),
                ("Pier North 2 (44C80F)", "Bắc",  3.250, 13.451, 2.950, 13.451),
                ("Pier North 2 (44C80F)", "Tây",  3.000, 13.451, 3.000, 13.151),

                // Feature 5: NW Corner 1-C Enclosure (Handles 44C7EF, 44C81C, 44C81E, 44C7F5)
                ("NW Corner 1-C", "Bắc ngoài",     0.850, 13.551, 0.200, 13.551),
                ("NW Corner 1-C", "Tây ngoài",     0.200, 13.551, 0.200, 12.650),
                ("NW Corner 1-C", "Nam ngoài",     0.200, 12.650, 0.650, 12.650),
                ("NW Corner 1-C", "Đông tới cột",  0.650, 12.650, 0.650, 12.900),
                ("NW Corner 1-C", "Đông ngoài",    0.850, 13.551, 0.850, 13.101),
                ("NW Corner 1-C", "Nam tới cột",   0.850, 13.101, 0.675, 13.101),

                // Feature 6: West Pier Upper at Y=11.75 (Handle 44C707)
                ("West Pier Upper (44C707)", "Tây",  0.300, 11.650, 0.300, 11.850),
                ("West Pier Upper (44C707)", "Bắc",  0.300, 11.800, 0.600, 11.800),
                ("West Pier Upper (44C707)", "Đông", 0.600, 11.850, 0.600, 11.650),
                ("West Pier Upper (44C707)", "Nam",  0.600, 11.700, 0.300, 11.700),

                // Feature 7: West Upper Chase at Y=10.60 (Handles 44C71B, 44C71C)
                ("West Chase Upper (44C71B/C)", "Bắc",  0.150, 10.852, 0.600, 10.852),
                ("West Chase Upper (44C71B/C)", "Đông", 0.600, 10.852, 0.600, 10.352),
                ("West Chase Upper (44C71B/C)", "Nam",  0.600, 10.352, 0.150, 10.352),
                ("West Chase Upper (44C71B/C)", "Tây",  0.150, 10.352, 0.150, 10.852),

                // Feature 8: West Lower Chase at Y=2.60 (Handles 44C625, 44C626)
                ("West Chase Lower (44C625/6)", "Bắc",  0.150, 2.848, 0.600, 2.848),
                ("West Chase Lower (44C625/6)", "Đông", 0.600, 2.848, 0.600, 2.348),
                ("West Chase Lower (44C625/6)", "Nam",  0.600, 2.348, 0.150, 2.348),
                ("West Chase Lower (44C625/6)", "Tây",  0.150, 2.348, 0.150, 2.848),

                // Feature 9: West Pier Lower at Y=1.45 (Handle 44C234)
                ("West Pier Lower (44C234)", "Tây",  0.300, 1.350, 0.300, 1.550),
                ("West Pier Lower (44C234)", "Bắc",  0.300, 1.500, 0.600, 1.500),
                ("West Pier Lower (44C234)", "Đông", 0.600, 1.550, 0.600, 1.350),
                ("West Pier Lower (44C234)", "Nam",  0.600, 1.400, 0.300, 1.400),

                // Feature 10: SW Corner 1-A Enclosure (Handles 44C6F5, 44C766, 44C768, 44C705)
                ("SW Corner 1-A", "Nam ngoài",     0.850, -0.351, 0.200, -0.351),
                ("SW Corner 1-A", "Tây ngoài",     0.200, -0.351, 0.200,  0.551),
                ("SW Corner 1-A", "Bắc ngoài",     0.200,  0.551, 0.650,  0.551),
                ("SW Corner 1-A", "Đông tới cột",  0.650,  0.551, 0.650,  0.300),
                ("SW Corner 1-A", "Đông ngoài",    0.850, -0.351, 0.850,  0.099),
                ("SW Corner 1-A", "Bắc tới cột",   0.850,  0.099, 0.675,  0.099),

                // Feature 11: Pier South 1 at X=1.90 (Handle 44C73D)
                ("Pier South 1 (44C73D)", "Bắc",  1.750,  0.049, 2.050,  0.049),
                ("Pier South 1 (44C73D)", "Đông", 2.000,  0.049, 2.000, -0.251),
                ("Pier South 1 (44C73D)", "Nam",  2.050, -0.251, 1.750, -0.251),
                ("Pier South 1 (44C73D)", "Tây",  1.800, -0.251, 1.800,  0.049),

                // Feature 12: Pier South 2 at X=3.10 (Handle 44C74A)
                ("Pier South 2 (44C74A)", "Bắc",  2.950,  0.049, 3.250,  0.049),
                ("Pier South 2 (44C74A)", "Đông", 3.200,  0.049, 3.200, -0.251),
                ("Pier South 2 (44C74A)", "Nam",  3.250, -0.251, 2.950, -0.251),
                ("Pier South 2 (44C74A)", "Tây",  3.000, -0.251, 3.000,  0.049),

                // Feature 13: South Entrance Pier Axis 2 (Handle 44C763)
                ("South Entrance Pier (44C763)", "Bắc",  4.150,  0.044, 5.550,  0.044),
                ("South Entrance Pier (44C763)", "Đông", 5.500,  0.044, 5.500, -0.256),
                ("South Entrance Pier (44C763)", "Nam",  5.550, -0.256, 4.150, -0.256),
                ("South Entrance Pier (44C763)", "Tây",  4.200, -0.256, 4.200,  0.044)
            };

            // 4. Idempotency cleanup: Remove previously created 100mm walls in these specific feature bounding boxes
            using (var txClean = new Transaction(doc, "Clean Previous 21 Handles Walls"))
            {
                txClean.Start();
                var opt = txClean.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new TwentyOneHandlesWarningSwallower());
                txClean.SetFailureHandlingOptions(opt);

                var old100Walls = new FilteredElementCollector(doc)
                    .OfClass(typeof(Wall))
                    .Cast<Wall>()
                    .Where(w => w.WallType.Name.Contains("100"))
                    .Where(w =>
                    {
                        var lc = w.Location as LocationCurve;
                        if (lc?.Curve is Line l)
                        {
                            var p0 = l.GetEndPoint(0) * FT2M;
                            var p1 = l.GetEndPoint(1) * FT2M;
                            double mx = (p0.X + p1.X) / 2.0;
                            double my = (p0.Y + p1.Y) / 2.0;

                            // Check West side zone: X < 6.0 and Y in [-0.5, 14.0]
                            if (mx >= 0.05 && mx <= 5.80 && my >= -0.50 && my <= 13.80) return true;
                            // Check Staircase 1 chase: X in [7.9, 8.6] and Y in [13.1, 13.9]
                            if (mx >= 7.90 && mx <= 8.60 && my >= 13.10 && my <= 13.90) return true;
                            // Check Staircase 2 chase: X in [29.1, 29.8] and Y in [13.1, 13.9]
                            if (mx >= 29.10 && mx <= 29.80 && my >= 13.10 && my <= 13.90) return true;
                        }
                        return false;
                    })
                    .ToList();

                foreach (var w in old100Walls)
                {
                    try { doc.Delete(w.Id); } catch { }
                }

                txClean.Commit();
            }

            // 5. Create all walls
            var createdWalls = new List<object>();
            var selIds = new List<ElementId>();

            using (var tx = new Transaction(doc, "Create Walls from 21 AutoCAD Handles"))
            {
                tx.Start();
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new TwentyOneHandlesWarningSwallower());
                tx.SetFailureHandlingOptions(opt);

                foreach (var def in wallDefs)
                {
                    var p1 = new XYZ(def.x1 * M2FT, def.y1 * M2FT, lvlTang1.Elevation);
                    var p2 = new XYZ(def.x2 * M2FT, def.y2 * M2FT, lvlTang1.Elevation);
                    var line = Line.CreateBound(p1, p2);

                    var wall = Wall.Create(doc, line, wt100.Id, lvlTang1.Id, heightFt, 0.0, false, false);
                    if (lvlTang2 != null)
                    {
                        wall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.Set(lvlTang2.Id);
                        wall.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET)?.Set(0.0);
                    }

                    createdWalls.Add(new
                    {
                        id = wall.Id.Value,
                        feature = def.feature,
                        name = def.name,
                        p1 = new { x = def.x1, y = def.y1 },
                        p2 = new { x = def.x2, y = def.y2 }
                    });

                    selIds.Add(wall.Id);
                }

                doc.Regenerate();
                tx.Commit();
            }

            // 6. Highlight and Export Verification Images
            try
            {
                uidoc.Selection.SetElementIds(selIds);
            }
            catch { }

            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == uidoc.ActiveView.Id);
            if (uiview != null)
            {
                // Zoom to West facade area
                XYZ pMin = new XYZ(-0.5 * M2FT, -1.0 * M2FT, 0.0);
                XYZ pMax = new XYZ(6.5 * M2FT, 14.5 * M2FT, 0.0);
                uiview.ZoomAndCenterRectangle(pMin, pMax);
            }

            string outImgPath = "C:\\Users\\nguyenbuu.DESKTOP-TOEFTR1\\.gemini\\antigravity\\brain\\16005848-1987-4ccc-a037-b18d9e878697\\revit_21handles_result.png";
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

            // Clean image without selection highlight
            string cleanImgPath = "C:\\Users\\nguyenbuu.DESKTOP-TOEFTR1\\.gemini\\antigravity\\brain\\16005848-1987-4ccc-a037-b18d9e878697\\revit_21handles_clean.png";
            if (File.Exists(cleanImgPath)) { try { File.Delete(cleanImgPath); } catch { } }
            try
            {
                uidoc.Selection.SetElementIds(new List<ElementId>());
                var expOptClean = new ImageExportOptions
                {
                    FilePath = cleanImgPath,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_300,
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 3000
                };
                doc.ExportImage(expOptClean);
            }
            catch { }

            return new
            {
                success = true,
                totalCreated = createdWalls.Count,
                wallType = wt100.Name,
                featuresCount = 13,
                exportImage = outImgPath,
                cleanImage = cleanImgPath
            };
        }
    }
}
