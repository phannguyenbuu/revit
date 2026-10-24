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
    public class ThreeWallsS4WarningSwallower : IFailuresPreprocessor
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

    public static class CreateThreeWallsAndWindowS4
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

            var wt200 = wallTypes.FirstOrDefault(w => w.Name == "gach200_xay moi" || w.Name == "gach200" || w.Name == "Tường 200");
            var wt100 = doc.GetElement(new ElementId(2361138)) as WallType
                     ?? wallTypes.FirstOrDefault(w => w.Name.Equals("gach100_xay moi", StringComparison.OrdinalIgnoreCase))
                     ?? wallTypes.FirstOrDefault(w => w.Name.Contains("100") && !w.Name.Contains("SENO", StringComparison.OrdinalIgnoreCase));

            if (wt200 == null) return new { error = "Wall type gach200_xay moi not found" };
            if (wt100 == null) return new { error = "Wall type gach100_xay moi not found" };


            // 2. Levels
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .ToList();

            var lvlTang1 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));
            var lvlTang2 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 2", StringComparison.OrdinalIgnoreCase));
            if (lvlTang1 == null) return new { error = "Level TẦNG 1 not found" };

            double heightFt = (lvlTang2 != null) ? (lvlTang2.Elevation - lvlTang1.Elevation) : (3.60 * M2FT);

            // 3. Find or create Window Symbol S4
            var allWindowSymbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Windows)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>()
                .ToList();

            FamilySymbol symS4 = allWindowSymbols.FirstOrDefault(s => s.Name == "S4_1500x1400");
            if (symS4 == null)
            {
                FamilySymbol baseSym = allWindowSymbols.FirstOrDefault(s => s.Name == "S1_1500x1400")
                                    ?? allWindowSymbols.FirstOrDefault(s => s.FamilyName.Contains("CUA SO 2 CANH NHOM KINH", StringComparison.OrdinalIgnoreCase))
                                    ?? allWindowSymbols.FirstOrDefault();
                if (baseSym == null) return new { error = "No base window family found to duplicate S4" };

                using (var txSym = new Transaction(doc, "Create S4 Symbol"))
                {
                    txSym.Start();
                    var opt = txSym.GetFailureHandlingOptions();
                    opt.SetFailuresPreprocessor(new ThreeWallsS4WarningSwallower());
                    txSym.SetFailureHandlingOptions(opt);

                    symS4 = baseSym.Duplicate("S4_1500x1400") as FamilySymbol;
                    symS4.get_Parameter(BuiltInParameter.WINDOW_WIDTH)?.Set(1.500 * M2FT);
                    symS4.get_Parameter(BuiltInParameter.WINDOW_HEIGHT)?.Set(1.400 * M2FT);
                    symS4.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)?.Set("S4");
                    if (!symS4.IsActive) symS4.Activate();
                    txSym.Commit();
                }
            }
            else if (!symS4.IsActive)
            {
                using (var txSym = new Transaction(doc, "Activate S4 Symbol"))
                {
                    txSym.Start();
                    symS4.Activate();
                    txSym.Commit();
                }
            }

            // 4. Clean previous runs in this zone (idempotency)
            using (var txClean = new Transaction(doc, "Clean Previous S4 Zone Elements"))
            {
                txClean.Start();
                var opt = txClean.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new ThreeWallsS4WarningSwallower());
                txClean.SetFailureHandlingOptions(opt);

                var oldWalls = new FilteredElementCollector(doc)
                    .OfClass(typeof(Wall))
                    .Cast<Wall>()
                    .Where(w =>
                    {
                        var lc = w.Location as LocationCurve;
                        if (lc?.Curve is Line l)
                        {
                            var p0 = l.GetEndPoint(0) * FT2M;
                            var p1 = l.GetEndPoint(1) * FT2M;
                            double mx = (p0.X + p1.X) / 2.0;
                            double my = (p0.Y + p1.Y) / 2.0;
                            // Check if along North wall Y ~ 13.203 and X in [33.4, 37.6]
                            if (Math.Abs(my - 13.203) < 0.2 && mx > 33.4 && mx < 37.6) return true;
                            // Check corner box X in [37.0, 37.6] and Y in [12.5, 13.2]
                            if (mx >= 36.95 && mx <= 37.65 && my >= 12.55 && my <= 13.25) return true;
                        }
                        return false;
                    })
                    .ToList();

                foreach (var w in oldWalls)
                {
                    try { doc.Delete(w.Id); } catch { }
                }

                txClean.Commit();
            }

            // 5. Create Walls and Window S4
            Wall northWall = null;
            FamilyInstance winInst = null;
            var cornerWalls = new List<Wall>();
            var selIds = new List<ElementId>();

            using (var tx = new Transaction(doc, "AI Copilot: Create 3 Walls and Window S4"))
            {
                tx.Start();
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new ThreeWallsS4WarningSwallower());
                tx.SetFailureHandlingOptions(opt);

                // 5a. North 200mm Exterior Wall: from X = 33.350 to X = 37.500, Y = 13.203
                var ptStartN = new XYZ(33.350 * M2FT, 13.203 * M2FT, lvlTang1.Elevation);
                var ptEndN   = new XYZ(37.500 * M2FT, 13.203 * M2FT, lvlTang1.Elevation);
                var lineN = Line.CreateBound(ptStartN, ptEndN);

                northWall = Wall.Create(doc, lineN, wt200.Id, lvlTang1.Id, heightFt, 0.0, false, false);
                if (lvlTang2 != null)
                {
                    northWall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.Set(lvlTang2.Id);
                    northWall.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET)?.Set(0.0);
                }
                selIds.Add(northWall.Id);

                // Regenerate so wall geometry exists for hosting window
                doc.Regenerate();

                // 5b. Place Window S4: center at X = 34.500, Y = 13.203, sill = 0.900m
                double sillM = 0.900;
                var winPt = new XYZ(34.500 * M2FT, 13.203 * M2FT, lvlTang1.Elevation + (sillM * M2FT));
                winInst = doc.Create.NewFamilyInstance(winPt, symS4, northWall, lvlTang1, StructuralType.NonStructural);

                if (winInst != null)
                {
                    var markParam = winInst.get_Parameter(BuiltInParameter.ALL_MODEL_MARK);
                    if (markParam != null && !markParam.IsReadOnly)
                    {
                        markParam.Set("S4");
                    }
                    var sillParam = winInst.get_Parameter(BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM);
                    if (sillParam != null && !sillParam.IsReadOnly)
                    {
                        sillParam.Set(sillM * M2FT);
                    }
                    selIds.Add(winInst.Id);
                }

                // 5c. Corner Walls (Enclosing Column B-6 / Pipe Chase at axis 6)
                // East wall: from (37.500, 13.203) to (37.500, 12.652) (100mm)
                // South wall: from (37.500, 12.652) to (37.100, 12.652) (100mm)
                // West wall: from (37.100, 12.652) to (37.100, 13.103) (100mm)
                var cornerSegments = new (string desc, double x1, double y1, double x2, double y2)[]
                {
                    ("Tường góc Đông (trục 6)", 37.500, 13.203, 37.500, 12.652),
                    ("Tường góc Nam",            37.500, 12.652, 37.100, 12.652),
                    ("Tường góc Tây (hộp gen)",   37.100, 12.652, 37.100, 12.900)
                };


                foreach (var seg in cornerSegments)
                {
                    var p1 = new XYZ(seg.x1 * M2FT, seg.y1 * M2FT, lvlTang1.Elevation);
                    var p2 = new XYZ(seg.x2 * M2FT, seg.y2 * M2FT, lvlTang1.Elevation);
                    var l = Line.CreateBound(p1, p2);
                    var cw = Wall.Create(doc, l, wt100.Id, lvlTang1.Id, heightFt, 0.0, false, false);
                    if (lvlTang2 != null)
                    {
                        cw.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.Set(lvlTang2.Id);
                        cw.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET)?.Set(0.0);
                    }
                    cornerWalls.Add(cw);
                    selIds.Add(cw.Id);
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
                XYZ pMin = new XYZ(32.5 * M2FT, 11.0 * M2FT, 0.0);
                XYZ pMax = new XYZ(38.5 * M2FT, 14.5 * M2FT, 0.0);
                uiview.ZoomAndCenterRectangle(pMin, pMax);
            }

            string outImgPath = "C:\\Users\\nguyenbuu.DESKTOP-TOEFTR1\\.gemini\\antigravity\\brain\\16005848-1987-4ccc-a037-b18d9e878697\\revit_3walls_1win_result.png";
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

            // Clean image without selection highlight
            string cleanImgPath = "C:\\Users\\nguyenbuu.DESKTOP-TOEFTR1\\.gemini\\antigravity\\brain\\16005848-1987-4ccc-a037-b18d9e878697\\revit_3walls_1win_clean.png";
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
                northWallId = northWall?.Id.Value,
                windowId = winInst?.Id.Value,
                windowTag = "S4",
                windowWidthMm = 1500,
                cornerWallsCount = cornerWalls.Count,
                cornerWallIds = cornerWalls.Select(w => w.Id.Value).ToList(),
                exportImage = outImgPath,
                cleanImage = cleanImgPath
            };
        }
    }
}
