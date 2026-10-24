using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class Hg1K2WarningSwallower : IFailuresPreprocessor
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

    public static class CreateHG1AndPierK2Walls
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

            var wt100 = wallTypes.FirstOrDefault(w => w.Name == "gach100_xay moi")
                     ?? wallTypes.FirstOrDefault(w => w.Name.Contains("100"));
            if (wt100 == null) return new { error = "WallType 100mm not found" };

            // 2. Levels
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .ToList();

            var lvlTang1 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));
            var lvlTang2 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 2", StringComparison.OrdinalIgnoreCase));
            if (lvlTang1 == null) return new { error = "Level TẦNG 1 not found" };

            double heightFt = (lvlTang2 != null) ? (lvlTang2.Elevation - lvlTang1.Elevation) : (3.60 * M2FT);

            // 3. Wall Definitions
            // HG1 (6 walls forming continuous loop):
            // C1(36.900, -0.350) -> C2(37.500, -0.350) -> C3(37.500, 0.550) -> C4(37.100, 0.550) -> C5(37.100, 0.050) -> C6(36.900, 0.050) -> C1
            //
            // Pier K2 (4 walls forming continuous loop):
            // P1(37.100, 1.552) -> P2(37.400, 1.552) -> P3(37.400, 1.752) -> P4(37.100, 1.752) -> P1

            var wallDefs = new List<(string name, double x1, double y1, double x2, double y2)>
            {
                // HG1
                ("HG1 - Tường Nam",          36.900, -0.350, 37.500, -0.350),
                ("HG1 - Tường Đông",         37.500, -0.350, 37.500,  0.550),
                ("HG1 - Tường Bắc",          37.500,  0.550, 37.100,  0.550),
                ("HG1 - Tường Bắc-Nam trong", 37.100,  0.550, 37.100,  0.050),
                ("HG1 - Tường Đông-Tây trong",37.100,  0.050, 36.900,  0.050),
                ("HG1 - Tường Tây ngoài",    36.900,  0.050, 36.900, -0.350),

                // Pier K2
                ("K2 - Tường Nam",  37.100, 1.552, 37.400, 1.552),
                ("K2 - Tường Đông", 37.400, 1.552, 37.400, 1.752),
                ("K2 - Tường Bắc",  37.400, 1.752, 37.100, 1.752),
                ("K2 - Tường Tây",  37.100, 1.752, 37.100, 1.552)
            };

            var createdWalls = new List<object>();
            var selIds = new List<ElementId>();

            using (var tx = new Transaction(doc, "Create HG1 and Pier K2 Walls 100mm"))
            {
                tx.Start();
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new Hg1K2WarningSwallower());
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

                    selIds.Add(wall.Id);
                    createdWalls.Add(new
                    {
                        id = wall.Id.Value,
                        name = def.name,
                        start = new { x = def.x1, y = def.y1 },
                        end = new { x = def.x2, y = def.y2 },
                        lengthM = line.Length * FT2M
                    });
                }

                tx.Commit();
            }

            // 4. Highlight & Export View
            try
            {
                uidoc.Selection.SetElementIds(selIds);
            }
            catch { }

            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == uidoc.ActiveView.Id);
            if (uiview != null)
            {
                XYZ pMin = new XYZ(36.0 * M2FT, -0.8 * M2FT, 0.0);
                XYZ pMax = new XYZ(38.2 * M2FT, 2.5 * M2FT, 0.0);
                uiview.ZoomAndCenterRectangle(pMin, pMax);
            }

            string outImgPath = "C:\\Users\\nguyenbuu.DESKTOP-TOEFTR1\\.gemini\\antigravity\\brain\\16005848-1987-4ccc-a037-b18d9e878697\\revit_hg1_k2_result.png";
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

            // Clean image without selection
            string cleanImgPath = "C:\\Users\\nguyenbuu.DESKTOP-TOEFTR1\\.gemini\\antigravity\\brain\\16005848-1987-4ccc-a037-b18d9e878697\\revit_hg1_k2_clean.png";
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
                    PixelSize = 2500
                };
                doc.ExportImage(expOptClean);
            }
            catch { }

            return new
            {
                success = true,
                totalCreated = createdWalls.Count,
                wallType = wt100.Name,
                walls = createdWalls,
                exportImage = outImgPath,
                cleanImage = cleanImgPath
            };
        }
    }
}
