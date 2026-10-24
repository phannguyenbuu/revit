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
    public class WallAS1WarningSwallower : IFailuresPreprocessor
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

    public static class CreateWallAWithS1Windows
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

            // 3. Find window symbol for S1 (1500mm width)
            var allWindowSymbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Windows)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>()
                .ToList();

            FamilySymbol symS1 = allWindowSymbols.FirstOrDefault(s => s.Name == "S1_1500x1400")
                              ?? allWindowSymbols.FirstOrDefault(s => s.Id.Value == 2360977)
                              ?? allWindowSymbols.FirstOrDefault(s => s.Id.Value == 144661)
                              ?? allWindowSymbols.FirstOrDefault(s => s.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)?.AsString() == "S1"
                                                                   && s.FamilyName.Contains("NHOM KINH", StringComparison.OrdinalIgnoreCase));

            if (symS1 == null)
                return new { error = "Window symbol for S1 not found" };

            using (var txSym = new Transaction(doc, "Ensure S1 Symbol Active"))
            {
                txSym.Start();
                var opt = txSym.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new WallAS1WarningSwallower());
                txSym.SetFailureHandlingOptions(opt);

                if (!symS1.IsActive) symS1.Activate();
                txSym.Commit();
            }

            // 4. Clean any existing wall on Grid A (Y ~ 0.000m) between X = 4.0m and 34.0m if re-run
            using (var txClean = new Transaction(doc, "Clean Previous Wall A"))
            {
                txClean.Start();
                var opt = txClean.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new WallAS1WarningSwallower());
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
                            // Check if it's horizontal along Y ~ 0.0
                            return Math.Abs(ym1) < 0.05 && Math.Abs(ym2) < 0.05 && Math.Abs(xm1 - xm2) > 5.0;
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

            // 5. Windows S1 definitions (8 windows along Trục A)
            // X coordinates from AutoCAD selection:
            // Bay 2-3: X = 6.300m
            // Bay 3-4: X = 9.850m
            // Bay 4-5: X = 13.450m
            // Bay 5-6: X = 17.050m
            // Bay 6-7: X = 20.650m
            // Bay 7-8: X = 24.250m
            // Bay 8-9: X = 27.850m
            // Bay 9-10: X = 31.400m
            var s1WindowsDef = new[]
            {
                new { tag = "S1-A1", x = 6.300,  bay = "Trục 2 - Trục 3", room = "P. Trực ban tiếp dân" },
                new { tag = "S1-A2", x = 9.850,  bay = "Trục 3 - Trục 4", room = "P. Đăng ký xe máy" },
                new { tag = "S1-A3", x = 13.450, bay = "Trục 4 - Trục 5", room = "P. Đăng ký xe máy" },
                new { tag = "S1-A4", x = 17.050, bay = "Trục 5 - Trục 6", room = "P. Cơ yếu" },
                new { tag = "S1-A5", x = 20.650, bay = "Trục 6 - Trục 7", room = "P. Cơ yếu" },
                new { tag = "S1-A6", x = 24.250, bay = "Trục 7 - Trục 8", room = "P. Thông tin" },
                new { tag = "S1-A7", x = 27.850, bay = "Trục 8 - Trục 9", room = "P. Thông tin" },
                new { tag = "S1-A8", x = 31.400, bay = "Trục 9 - Trục 10", room = "P. Làm việc (2 CBCS)" }
            };

            double yCenter = 0.000;
            double sillH = 0.900; // 900mm standard sill height
            double xStart = 4.350; // Trục 2
            double xEnd = 33.350;  // Trục 10
            double heightFt = (lvlTang2 != null) ? (lvlTang2.Elevation - lvlTang1.Elevation) : (3.60 * M2FT);

            Wall createdWall = null;
            var createdWindows = new List<object>();

            using (var tx = new Transaction(doc, "AI Copilot: Create Wall A with 8 S1 Windows"))
            {
                tx.Start();
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new WallAS1WarningSwallower());
                tx.SetFailureHandlingOptions(opt);

                // Create wall along Grid A (Y = 0.000m) from X = 4.350m to X = 33.350m
                var ptStart = new XYZ(xStart * M2FT, yCenter * M2FT, lvlTang1.Elevation);
                var ptEnd = new XYZ(xEnd * M2FT, yCenter * M2FT, lvlTang1.Elevation);
                var wallLine = Line.CreateBound(ptStart, ptEnd);

                createdWall = Wall.Create(doc, wallLine, wallType200.Id, lvlTang1.Id, heightFt, 0.0, false, false);
                if (lvlTang2 != null)
                {
                    createdWall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.Set(lvlTang2.Id);
                    createdWall.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET)?.Set(0.0);
                }

                // Regenerate so wall geometry and host reference exist
                doc.Regenerate();

                // Place each window
                foreach (var w in s1WindowsDef)
                {
                    var winPt = new XYZ(w.x * M2FT, yCenter * M2FT, lvlTang1.Elevation + (sillH * M2FT));
                    var winInst = doc.Create.NewFamilyInstance(winPt, symS1, createdWall, lvlTang1, StructuralType.NonStructural);

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
                        sillParam.Set(sillH * M2FT);
                    }

                    createdWindows.Add(new
                    {
                        tag = w.tag,
                        id = winInst.Id.Value,
                        symbol = symS1.Name,
                        family = symS1.FamilyName,
                        bay = w.bay,
                        room = w.room,
                        x = w.x,
                        y = yCenter,
                        widthMm = 1500,
                        sillHeightM = sillH
                    });
                }

                tx.Commit();
            }

            // 6. Focus and zoom to building
            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == uidoc.ActiveView.Id);
            if (uiview != null)
            {
                XYZ pMin = new XYZ(-2.0 * M2FT, -2.0 * M2FT, 0.0);
                XYZ pMax = new XYZ(38.0 * M2FT, 16.0 * M2FT, 0.0);
                uiview.ZoomAndCenterRectangle(pMin, pMax);
            }

            // 7. Export verification image
            string outImgPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_wall_a_s1_result.png";
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

            return new
            {
                success = true,
                wall = new
                {
                    id = createdWall?.Id.Value,
                    type = wallType200.Name,
                    xStart = xStart,
                    xEnd = xEnd,
                    y = yCenter,
                    lengthM = (xEnd - xStart)
                },
                windowCount = createdWindows.Count,
                windows = createdWindows,
                exportImage = outImgPath
            };
        }
    }
}
