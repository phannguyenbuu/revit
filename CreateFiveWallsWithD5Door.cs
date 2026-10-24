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
    public class FiveWallsWarningSwallower : IFailuresPreprocessor
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

    public static class CreateFiveWallsWithD5Door
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

            // 3. Door Symbol D5_800x2200
            var allDoorSymbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>()
                .ToList();

            FamilySymbol symD5 = allDoorSymbols.FirstOrDefault(s => s.Name == "D5_800x2200")
                              ?? allDoorSymbols.FirstOrDefault(s => s.Id.Value == 1671711);

            if (symD5 == null)
            {
                var baseSym = allDoorSymbols.FirstOrDefault(s => s.FamilyName.Contains("EROWINDOW", StringComparison.OrdinalIgnoreCase));
                if (baseSym != null)
                {
                    using (var txSym = new Transaction(doc, "Prepare D5"))
                    {
                        txSym.Start();
                        symD5 = baseSym.Duplicate("D5_800x2200") as FamilySymbol;
                        symD5.get_Parameter(BuiltInParameter.DOOR_WIDTH)?.Set(0.800 * M2FT);
                        symD5.get_Parameter(BuiltInParameter.DOOR_HEIGHT)?.Set(2.200 * M2FT);
                        symD5.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)?.Set("D5");
                        if (!symD5.IsActive) symD5.Activate();
                        txSym.Commit();
                    }
                }
            }

            if (symD5 != null && !symD5.IsActive)
            {
                using (var txAct = new Transaction(doc, "Activate D5"))
                {
                    txAct.Start();
                    symD5.Activate();
                    txAct.Commit();
                }
            }

            // 4. Definitions of the 5 walls:
            // Wall 1: Vách cửa D5 (100mm) dọc X = 34.600m từ Y = 7.800m đến Y = 9.450m
            // Wall 2: Tường đáy WC Nữ dọc Trục C (200mm) từ X = 34.600m đến X = 37.100m, Y = 7.800m
            // Wall 3: Vách trái HG4 / vách phải WC Nữ (100mm) dọc X = 37.100m từ Y = 7.800m đến Y = 10.450m
            // Wall 4: Vách đỉnh HG4 (100mm) từ X = 37.100m đến X = 37.500m, Y = 10.450m
            // Wall 5: Vách phải HG4 (100mm) dọc X = 37.500m từ Y = 7.800m đến Y = 10.450m
            var wallDefs = new[]
            {
                new { name = "Vách cửa D5", type = wallType100, x1 = 34.600, y1 = 7.800, x2 = 34.600, y2 = 9.450 },
                new { name = "Tường đáy Trục C", type = wallType200, x1 = 34.600, y1 = 7.800, x2 = 37.100, y2 = 7.800 },
                new { name = "Vách trái HG4", type = wallType100, x1 = 37.100, y1 = 7.800, x2 = 37.100, y2 = 10.450 },
                new { name = "Vách đỉnh HG4", type = wallType100, x1 = 37.100, y1 = 10.450, x2 = 37.500, y2 = 10.450 },
                new { name = "Vách phải HG4", type = wallType100, x1 = 37.500, y1 = 7.800, x2 = 37.500, y2 = 10.450 }
            };

            double heightFt = (lvlTang2 != null) ? (lvlTang2.Elevation - lvlTang1.Elevation) : (3.60 * M2FT);
            var createdWalls = new List<object>();
            Wall doorHostWall = null;
            FamilyInstance createdDoor = null;

            using (var tx = new Transaction(doc, "AI Copilot: Create 5 Walls and Door D5"))
            {
                tx.Start();
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new FiveWallsWarningSwallower());
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

                    if (wd.name == "Vách cửa D5")
                    {
                        doorHostWall = wall;
                    }

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

                // Regenerate so doorHostWall geometry is ready
                doc.Regenerate();

                // Place door D5 on Wall 1 at X = 34.600m, Y = 8.900m
                if (doorHostWall != null && symD5 != null)
                {
                    double xDoor = 34.600;
                    double yDoor = 8.900;
                    var doorPt = new XYZ(xDoor * M2FT, yDoor * M2FT, lvlTang1.Elevation);
                    createdDoor = doc.Create.NewFamilyInstance(doorPt, symD5, doorHostWall, lvlTang1, StructuralType.NonStructural);

                    createdDoor.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.Set("D5");

                    // Door swing: in AutoCAD, swings into WC Nữ (+X direction) with hinge at south (Y = 8.502)
                    var facing = createdDoor.FacingOrientation;
                    if (facing.X < 0)
                    {
                        createdDoor.flipFacing();
                    }

                    var hand = createdDoor.HandOrientation;
                    if (hand.Y < 0)
                    {
                        createdDoor.flipHand();
                    }
                }

                tx.Commit();
            }

            // 5. Focus view on WC zone
            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == uidoc.ActiveView.Id);
            if (uiview != null)
            {
                XYZ pMin = new XYZ(31.0 * M2FT, 6.5 * M2FT, 0.0);
                XYZ pMax = new XYZ(38.5 * M2FT, 12.0 * M2FT, 0.0);
                uiview.ZoomAndCenterRectangle(pMin, pMax);
            }

            // 6. Export verification image
            string outImgPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_5walls_d5_result.png";
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
                door = createdDoor != null ? new
                {
                    id = createdDoor.Id.Value,
                    symbol = symD5.Name,
                    mark = "D5",
                    x = 34.600,
                    y = 8.900,
                    widthMm = 800,
                    heightMm = 2200
                } : null,
                exportImage = outImgPath
            };
        }
    }
}
