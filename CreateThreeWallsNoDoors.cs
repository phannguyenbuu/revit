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
    public class ThreeWallsWarningSwallower : IFailuresPreprocessor
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

    public static class CreateThreeWallsNoDoors
    {
        private const double M2FT = 3.2808398950131235;
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active Revit doc" };

            // 1. Get Wall Types
            var wallTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(WallType))
                .Cast<WallType>()
                .ToList();

            var wallType100 = wallTypes.FirstOrDefault(w => w.Name == "gach100_xay moi")
                           ?? wallTypes.FirstOrDefault(w => w.Name == "gach100");
            var wallType200 = wallTypes.FirstOrDefault(w => w.Name == "gach200_xay moi")
                           ?? wallTypes.FirstOrDefault(w => w.Name == "gach200");

            if (wallType100 == null) return new { error = "Wall type gach100_xay moi not found" };
            if (wallType200 == null) return new { error = "Wall type gach200_xay moi not found" };

            // 2. Levels
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .ToList();

            var lvlTang1 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));
            var lvlTang2 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 2", StringComparison.OrdinalIgnoreCase));
            if (lvlTang1 == null) return new { error = "Level TẦNG 1 not found" };

            // 3. Wall definitions
            var wallDefs = new[]
            {
                new { name = "Tường Trục B", type = wallType200, x1 = 36.150, y1 = 5.400, x2 = 37.150, y2 = 5.400 },
                new { name = "Vách trái HG", type = wallType100, x1 = 37.100, y1 = 2.750, x2 = 37.100, y2 = 5.400 },
                new { name = "Vách đáy HG",  type = wallType100, x1 = 37.100, y1 = 2.750, x2 = 37.500, y2 = 2.750 },
                new { name = "Vách phải HG", type = wallType100, x1 = 37.500, y1 = 2.750, x2 = 37.500, y2 = 5.400 }
            };

            double heightFt = (lvlTang2 != null) ? (lvlTang2.Elevation - lvlTang1.Elevation) : (3.60 * M2FT);
            var createdWalls = new List<object>();
            var wallIds = new List<ElementId>();

            using (var tx = new Transaction(doc, "AI Copilot: Create Selected Walls (No Doors)"))
            {
                tx.Start();
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new ThreeWallsWarningSwallower());
                tx.SetFailureHandlingOptions(opt);

                foreach (var wd in wallDefs)
                {
                    var p0 = new XYZ(wd.x1 * M2FT, wd.y1 * M2FT, lvlTang1.Elevation);
                    var p1 = new XYZ(wd.x2 * M2FT, wd.y2 * M2FT, lvlTang1.Elevation);
                    var line = Line.CreateBound(p0, p1);

                    var wall = Wall.Create(doc, line, wd.type.Id, lvlTang1.Id, heightFt, 0.0, false, false);
                    if (lvlTang2 != null)
                    {
                        wall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.Set(lvlTang2.Id);
                        wall.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET)?.Set(0.0);
                    }

                    wallIds.Add(wall.Id);
                    createdWalls.Add(new
                    {
                        name = wd.name,
                        id = wall.Id.Value,
                        type = wd.type.Name,
                        start = new { x = wd.x1, y = wd.y1 },
                        end = new { x = wd.x2, y = wd.y2 },
                        lengthM = line.Length * FT2M
                    });
                }

                doc.Regenerate();
                tx.Commit();
            }

            // 4. Select created walls
            try
            {
                uidoc.Selection.SetElementIds(wallIds);
            }
            catch { }

            // 5. Focus view on zone
            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == uidoc.ActiveView.Id);
            if (uiview != null)
            {
                XYZ pMin = new XYZ(33.0 * M2FT, 1.5 * M2FT, 0.0);
                XYZ pMax = new XYZ(39.0 * M2FT, 6.5 * M2FT, 0.0);
                uiview.ZoomAndCenterRectangle(pMin, pMax);
            }

            // 6. Export verification image
            string outImgPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_3walls_result.png";
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
                wallCount = createdWalls.Count,
                walls = createdWalls,
                doorCount = 0,
                exportImage = outImgPath
            };
        }
    }
}
