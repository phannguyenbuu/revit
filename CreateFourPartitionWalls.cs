using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class FourWallsWarningSwallower : IFailuresPreprocessor
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

    public static class CreateFourPartitionWalls
    {
        private const double M2FT = 3.2808398950131235;
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active Revit doc" };

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

            // 3. The 4 partition walls along Trục 3, 5, 7, 9
            // Running from Grid A (Y = 0.000m) to Grid B (Y = 5.400m)
            var wallXCoords = new[]
            {
                new { Name = "Tường Trục 3", X = 8.050, Grid = "3" },
                new { Name = "Tường Trục 5", X = 15.250, Grid = "5" },
                new { Name = "Tường Trục 7", X = 22.450, Grid = "7" },
                new { Name = "Tường Trục 9", X = 29.650, Grid = "9" }
            };

            double zFt = lvlTang1.Elevation;
            double yStartFt = 0.000 * M2FT; // Grid A
            double yEndFt = 5.400 * M2FT;   // Grid B
            double heightFt = (lvlTang2 != null) ? (lvlTang2.Elevation - lvlTang1.Elevation) : (3.60 * M2FT);

            var createdWalls = new List<object>();

            using (var tx = new Transaction(doc, "AI Copilot: Create 4 Partition Walls (Trục 3, 5, 7, 9)"))
            {
                tx.Start();
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new FourWallsWarningSwallower());
                tx.SetFailureHandlingOptions(opt);

                foreach (var wInfo in wallXCoords)
                {
                    double xFt = wInfo.X * M2FT;
                    XYZ p0 = new XYZ(xFt, yStartFt, zFt);
                    XYZ p1 = new XYZ(xFt, yEndFt, zFt);
                    Line wallLine = Line.CreateBound(p0, p1);

                    var wall = Wall.Create(doc, wallLine, wallType200.Id, lvlTang1.Id, heightFt, 0.0, false, false);
                    if (lvlTang2 != null)
                    {
                        wall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.Set(lvlTang2.Id);
                        wall.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET)?.Set(0.0);
                    }

                    createdWalls.Add(new
                    {
                        id = wall.Id.Value,
                        name = wInfo.Name,
                        grid = wInfo.Grid,
                        x = wInfo.X,
                        yStart = 0.000,
                        yEnd = 5.400,
                        lengthM = wallLine.Length * FT2M
                    });
                }

                tx.Commit();
            }

            // 4. Export verification image
            string outImgPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_four_walls_result.png";
            try
            {
                var activeView = uidoc.ActiveView;
                var expOpt = new ImageExportOptions
                {
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 2560,
                    FilePath = outImgPath,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_300,
                    ExportRange = ExportRange.VisibleRegionOfCurrentView
                };
                doc.ExportImage(expOpt);
            }
            catch { }

            return new
            {
                success = true,
                count = createdWalls.Count,
                walls = createdWalls,
                exportImage = outImgPath
            };
        }
    }
}
