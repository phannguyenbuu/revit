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
    public class D5WarningSwallower : IFailuresPreprocessor
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

    public static class CreateWallWithD5Door
    {
        private const double M2FT = 3.2808398950131235;
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active Revit doc" };

            // 1. Get 100mm wall type
            var wallType100 = new FilteredElementCollector(doc)
                .OfClass(typeof(WallType))
                .Cast<WallType>()
                .FirstOrDefault(w => w.Name == "gach100_xay moi");

            if (wallType100 == null)
                return new { error = "Wall type gach100_xay moi not found" };

            // 2. Levels
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .ToList();

            var lvlTang1 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));
            var lvlTang2 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 2", StringComparison.OrdinalIgnoreCase));
            if (lvlTang1 == null) return new { error = "Level TẦNG 1 not found" };

            // 3. Find or duplicate door symbol for D5 (800mm width x 2200mm height)
            var allDoorSymbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>()
                .ToList();

            FamilySymbol baseSym = allDoorSymbols.FirstOrDefault(s => s.Id.Value == 1671711)
                                ?? allDoorSymbols.FirstOrDefault(s => s.FamilyName.Contains("EROWINDOW", StringComparison.OrdinalIgnoreCase) && s.FamilyName.Contains("1 CÁNH", StringComparison.OrdinalIgnoreCase))
                                ?? allDoorSymbols.FirstOrDefault(s => s.FamilyName.Contains("cua 1 canh", StringComparison.OrdinalIgnoreCase));

            if (baseSym == null)
                return new { error = "Base door symbol for 1 cánh not found" };

            FamilySymbol symD5 = allDoorSymbols.FirstOrDefault(s => s.Name == "D5_800x2200");
            using (var txSym = new Transaction(doc, "Prepare D5 Door Symbol"))
            {
                txSym.Start();
                var opt = txSym.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new D5WarningSwallower());
                txSym.SetFailureHandlingOptions(opt);

                if (symD5 == null)
                {
                    symD5 = baseSym.Duplicate("D5_800x2200") as FamilySymbol;
                    var pW = symD5.get_Parameter(BuiltInParameter.DOOR_WIDTH);
                    if (pW != null && !pW.IsReadOnly) pW.Set(0.800 * M2FT);
                    var pH = symD5.get_Parameter(BuiltInParameter.DOOR_HEIGHT);
                    if (pH != null && !pH.IsReadOnly) pH.Set(2.200 * M2FT);
                    var pTM = symD5.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK);
                    if (pTM != null && !pTM.IsReadOnly) pTM.Set("D5");
                }

                if (!symD5.IsActive) symD5.Activate();
                txSym.Commit();
            }

            // 4. Clean any existing wall near this location if re-running
            using (var txClean = new Transaction(doc, "Clean Previous D5 Wall"))
            {
                txClean.Start();
                var opt = txClean.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new D5WarningSwallower());
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
                            double xm1 = p1.X * FT2M;
                            double xm2 = p2.X * FT2M;
                            return Math.Abs(ym1 - 9.450) < 0.10 && Math.Abs(ym2 - 9.450) < 0.10 && xm1 > 33.0 && xm2 > 33.0;
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

            // 5. Create 100mm wall from X = 33.350m to X = 37.050m along Y = 9.450m
            double yCenter = 9.450;
            double xStart = 33.350;
            double xEnd = 37.050;
            double heightFt = (lvlTang2 != null) ? (lvlTang2.Elevation - lvlTang1.Elevation) : (3.60 * M2FT);

            Wall createdWall = null;
            FamilyInstance createdDoor = null;

            using (var tx = new Transaction(doc, "AI Copilot: Create WC Wall with Door D5"))
            {
                tx.Start();
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new D5WarningSwallower());
                tx.SetFailureHandlingOptions(opt);

                var ptStart = new XYZ(xStart * M2FT, yCenter * M2FT, lvlTang1.Elevation);
                var ptEnd = new XYZ(xEnd * M2FT, yCenter * M2FT, lvlTang1.Elevation);
                var wallLine = Line.CreateBound(ptStart, ptEnd);

                createdWall = Wall.Create(doc, wallLine, wallType100.Id, lvlTang1.Id, heightFt, 0.0, false, false);
                if (lvlTang2 != null)
                {
                    createdWall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.Set(lvlTang2.Id);
                    createdWall.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET)?.Set(0.0);
                }

                // Regenerate so wall geometry exists for hosting
                doc.Regenerate();

                // 6. Place door D5 at X = 33.950m, Y = 9.450m
                double xDoor = 33.950;
                var doorPt = new XYZ(xDoor * M2FT, yCenter * M2FT, lvlTang1.Elevation);
                createdDoor = doc.Create.NewFamilyInstance(doorPt, symD5, createdWall, lvlTang1, StructuralType.NonStructural);

                // Set Mark
                var markParam = createdDoor.get_Parameter(BuiltInParameter.ALL_MODEL_MARK);
                if (markParam != null && !markParam.IsReadOnly)
                {
                    markParam.Set("D5");
                }

                // Orientation: in AutoCAD, the door swings upward into +Y (WC Nam) with hinge on the left (X = 33.550)
                // Check FacingOrientation
                var facing = createdDoor.FacingOrientation;
                if (facing.Y < 0)
                {
                    createdDoor.flipFacing();
                }

                // Check HandOrientation (points from hinge to latch)
                // If hinge is on left (X=33.55), hand should point along +X
                var hand = createdDoor.HandOrientation;
                if (hand.X < 0)
                {
                    createdDoor.flipHand();
                }

                tx.Commit();
            }

            // 7. Focus on WC zone
            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == uidoc.ActiveView.Id);
            if (uiview != null)
            {
                XYZ pMin = new XYZ(31.0 * M2FT, 7.0 * M2FT, 0.0);
                XYZ pMax = new XYZ(38.0 * M2FT, 13.0 * M2FT, 0.0);
                uiview.ZoomAndCenterRectangle(pMin, pMax);
            }

            // 8. Export verification image
            string outImgPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_wall_d5_wc_result.png";
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
                wall = new
                {
                    id = createdWall?.Id.Value,
                    type = wallType100.Name,
                    xStart = xStart,
                    xEnd = xEnd,
                    y = yCenter,
                    lengthM = (xEnd - xStart),
                    thicknessMm = 100
                },
                door = new
                {
                    id = createdDoor?.Id.Value,
                    symbol = symD5.Name,
                    family = symD5.FamilyName,
                    mark = "D5",
                    x = 33.950,
                    y = yCenter,
                    widthMm = 800,
                    heightMm = 2200,
                    facing = createdDoor != null ? new { x = createdDoor.FacingOrientation.X, y = createdDoor.FacingOrientation.Y } : null,
                    hand = createdDoor != null ? new { x = createdDoor.HandOrientation.X, y = createdDoor.HandOrientation.Y } : null
                },
                exportImage = outImgPath
            };
        }
    }
}
