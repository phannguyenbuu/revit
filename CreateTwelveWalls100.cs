using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class TwelveWallsWarningSwallower : IFailuresPreprocessor
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

    public static class CreateTwelveWalls100
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

            // 3. Define the 12 walls (centerlines in meters)
            // Pier 1 (Left): X in [32.150, 33.550], Y in [-0.306, 0.094]
            // Pier 2 (Mid):  X in [34.450, 34.750], Y in [-0.301, 0.099]
            // Pier 3 (Right): X in [35.650, 35.950], Y in [-0.301, 0.099]
            var wallDefs = new List<(string name, double x1, double y1, double x2, double y2)>
            {
                // Box 1 (Pier trái X=32.15 -> 33.55)
                ("Tường 1-1 (Bắc Pier 1)", 32.150, 0.044, 33.550, 0.044),
                ("Tường 1-2 (Đông Pier 1)", 33.500, 0.044, 33.500, -0.256),
                ("Tường 1-3 (Nam Pier 1)",  33.550, -0.256, 32.150, -0.256),
                ("Tường 1-4 (Tây Pier 1)",  32.200, -0.256, 32.200, 0.044),

                // Box 2 (Pier giữa X=34.45 -> 34.75)
                ("Tường 2-1 (Bắc Pier 2)", 34.450, 0.049, 34.750, 0.049),
                ("Tường 2-2 (Đông Pier 2)", 34.700, 0.049, 34.700, -0.251),
                ("Tường 2-3 (Nam Pier 2)",  34.750, -0.251, 34.450, -0.251),
                ("Tường 2-4 (Tây Pier 2)",  34.500, -0.251, 34.500, 0.049),

                // Box 3 (Pier phải X=35.65 -> 35.95)
                ("Tường 3-1 (Bắc Pier 3)", 35.650, 0.049, 35.950, 0.049),
                ("Tường 3-2 (Đông Pier 3)", 35.900, 0.049, 35.900, -0.251),
                ("Tường 3-3 (Nam Pier 3)",  35.950, -0.251, 35.650, -0.251),
                ("Tường 3-4 (Tây Pier 3)",  35.700, -0.251, 35.700, 0.049)
            };

            var createdWalls = new List<object>();
            var selIds = new List<ElementId>();

            using (var tx = new Transaction(doc, "Create 12 Walls 100mm from CAD Selection"))
            {
                tx.Start();
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new TwelveWallsWarningSwallower());
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
                XYZ pMin = new XYZ(31.5 * M2FT, -0.8 * M2FT, 0.0);
                XYZ pMax = new XYZ(37.5 * M2FT, 1.2 * M2FT, 0.0);
                uiview.ZoomAndCenterRectangle(pMin, pMax);
            }

            string outImgPath = "C:\\Users\\nguyenbuu.DESKTOP-TOEFTR1\\.gemini\\antigravity\\brain\\16005848-1987-4ccc-a037-b18d9e878697\\revit_12walls100_result.png";
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

            return new
            {
                success = true,
                totalCreated = createdWalls.Count,
                wallType = wt100.Name,
                walls = createdWalls,
                exportImage = outImgPath
            };
        }
    }
}
