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
    public static class CreateWallWithDoors
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

            // 3. Find door symbols for D1 (1000mm 1-canh) and D7 (1200mm 2-canh)
            var allDoorSymbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>()
                .ToList();

            // Candidate for D1 (1 cánh, 1000mm)
            // Symbol 131952: "CUA ĐI GỖ 1 CANH O O THOANG" -> "CUA ĐI 1 CANH O O THOANG" (W=1000mm, H=2400mm)
            // or Symbol 2075619: "CD1C-EW-900X2200" -> "CD1C-EW2-900X2200" (W=1000mm, H=2000mm)
            // or Symbol 2070931: "cua 1 canh" -> "cua 1 canh" (W=900mm)
            var symD1 = allDoorSymbols.FirstOrDefault(s => s.Id.Value == 131952)
                     ?? allDoorSymbols.FirstOrDefault(s => s.Id.Value == 2075619)
                     ?? allDoorSymbols.FirstOrDefault(s => s.FamilyName.Contains("1 CANH", StringComparison.OrdinalIgnoreCase) && s.get_Parameter(BuiltInParameter.DOOR_WIDTH)?.AsDouble() * FT2M >= 0.95)
                     ?? allDoorSymbols.FirstOrDefault(s => s.FamilyName.Contains("cua 1 canh", StringComparison.OrdinalIgnoreCase));

            // Candidate for D7 (2 cánh, 1200mm)
            // Symbol 142632: "CUA ĐI 2 CANH NHOM KINH O O THOANG" -> "CUA ĐI NHOM KINH 2 CANH O O THOANG" (W=1200mm, H=2400mm)
            // or Symbol 2169541: "CỬA 2 CÁNH EROWINDOW(có ô chết)" -> "CỬA 2 CÁNH EROWINDOW 1600x2200mm 2" (W=1200mm, H=2200mm)
            var symD7 = allDoorSymbols.FirstOrDefault(s => s.Id.Value == 142632)
                     ?? allDoorSymbols.FirstOrDefault(s => s.Id.Value == 2169541)
                     ?? allDoorSymbols.FirstOrDefault(s => s.FamilyName.Contains("2 CANH", StringComparison.OrdinalIgnoreCase));

            if (symD1 == null) return new { error = "Door symbol for D1 not found" };
            if (symD7 == null) return new { error = "Door symbol for D7 not found" };

            // 4. Door locations and swing specs:
            // Wall is along Y = 7.800m, from X = 4.350m (Trục 2) to X = 33.350m (Trục 10)
            // Doors:
            // 1: D7 at X = 5.150m,  swing North (into room/stair), left hand
            // 2: D1 at X = 8.887m,  swing North (into P. Y Tế), left hand
            // 3: D1 at X = 15.987m, swing North (into P. Lấy lời khai), left hand
            // 4: D1 at X = 20.912m, swing South (into corridor), right hand
            // 5: D1 at X = 23.362m, swing South (into corridor), left hand
            // 6: D1 at X = 24.837m, swing North (into P. Điều tra), left hand
            // 7: D1 at X = 28.912m, swing North (into Kho tang vật), left hand
            // 8: D7 at X = 32.550m, swing North (into stair), right hand
            var doorsDef = new[]
            {
                new { tag = "D7-1", sym = symD7, x = 5.150,  openNorth = true,  flipHand = false },
                new { tag = "D1-1", sym = symD1, x = 8.887,  openNorth = true,  flipHand = false },
                new { tag = "D1-2", sym = symD1, x = 15.987, openNorth = true,  flipHand = false },
                new { tag = "D1-3", sym = symD1, x = 20.912, openNorth = false, flipHand = true  },
                new { tag = "D1-4", sym = symD1, x = 23.362, openNorth = false, flipHand = false },
                new { tag = "D1-5", sym = symD1, x = 24.837, openNorth = true,  flipHand = false },
                new { tag = "D1-6", sym = symD1, x = 28.912, openNorth = true,  flipHand = false },
                new { tag = "D7-2", sym = symD7, x = 32.550, openNorth = true,  flipHand = true  }
            };

            // Remove any previous wall along Grid C created by this script if exists
            // by checking existing walls along Y ~ 7.800
            using (var tx = new Transaction(doc, "Clean Previous Wall C"))
            {
                tx.Start();
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
                            return Math.Abs(ym1 - 7.800) < 0.05 && Math.Abs(ym2 - 7.800) < 0.05;
                        }
                        return false;
                    })
                    .ToList();

                foreach (var w in oldWalls)
                {
                    doc.Delete(w.Id);
                }
                tx.Commit();
            }

            Wall createdWall = null;
            var createdDoors = new List<object>();
            var selectionIds = new List<ElementId>();

            using (var tx = new Transaction(doc, "Create Wall 200 on Grid C with 8 Doors"))
            {
                tx.Start();

                // Activate symbols if needed
                if (!symD1.IsActive) symD1.Activate();
                if (!symD7.IsActive) symD7.Activate();
                doc.Regenerate();

                // Create wall along Grid C (Y = 7.800m) from X = 4.350m to X = 33.350m
                double yCenter = 7.800;
                var ptStart = new XYZ(4.350 * M2FT, yCenter * M2FT, 0.0);
                var ptEnd = new XYZ(33.350 * M2FT, yCenter * M2FT, 0.0);
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

                // Place each door
                foreach (var d in doorsDef)
                {
                    var doorPt = new XYZ(d.x * M2FT, yCenter * M2FT, 0.0);
                    var doorInst = doc.Create.NewFamilyInstance(doorPt, d.sym, createdWall, lvlTang1, StructuralType.NonStructural);

                    // Set Mark parameter
                    var markParam = doorInst.get_Parameter(BuiltInParameter.ALL_MODEL_MARK);
                    if (markParam != null && !markParam.IsReadOnly)
                    {
                        markParam.Set(d.tag);
                    }

                    // Check facing orientation
                    // In Revit, for wall along X direction (from West to East):
                    // Normal / Facing is perpendicular (along Y).
                    // If openNorth is true, Facing should point +Y (North).
                    // If openNorth is false, Facing should point -Y (South).
                    doc.Regenerate();

                    var facing = doorInst.FacingOrientation;
                    if (d.openNorth && facing.Y < 0)
                    {
                        doorInst.flipFacing();
                    }
                    else if (!d.openNorth && facing.Y > 0)
                    {
                        doorInst.flipFacing();
                    }

                    if (d.flipHand)
                    {
                        doorInst.flipHand();
                    }

                    selectionIds.Add(doorInst.Id);
                    createdDoors.Add(new
                    {
                        tag = d.tag,
                        id = doorInst.Id.Value,
                        symbol = d.sym.Name,
                        family = d.sym.FamilyName,
                        x = d.x,
                        y = yCenter
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
                    var minPt = new XYZ(2.0 * M2FT, 3.0 * M2FT, 0.0);
                    var maxPt = new XYZ(36.0 * M2FT, 12.0 * M2FT, 0.0);
                    uiview?.ZoomAndCenterRectangle(minPt, maxPt);
                }
            }
            catch { }

            // Export high-res detail image of the new wall and doors
            string outImg = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_wall_c_doors_result.png";
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
                doorsCount = createdDoors.Count,
                doors = createdDoors,
                exportedImage = outImg
            };
        }
    }
}
