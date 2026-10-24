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
    public class K3WarningSwallower : IFailuresPreprocessor
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

    public static class CreateStairWallsWithK3
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

            // 3. Find base window symbol and create duplicate K3 (Width 3100mm, Height 2100mm)
            var allWindowSymbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Windows)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>()
                .ToList();

            FamilySymbol baseSym = allWindowSymbols.FirstOrDefault(s => s.Id.Value == 144661) // CUA SO 2 CANH NHOM KINH
                                ?? allWindowSymbols.FirstOrDefault(s => s.FamilyName.Contains("NHOM KINH", StringComparison.OrdinalIgnoreCase))
                                ?? allWindowSymbols.FirstOrDefault(s => s.FamilyName.Contains("2 CANH", StringComparison.OrdinalIgnoreCase))
                                ?? allWindowSymbols.FirstOrDefault();

            if (baseSym == null) return new { error = "No base window symbol found" };

            FamilySymbol symK3 = null;
            using (var txSym = new Transaction(doc, "Prepare K3 Symbol"))
            {
                txSym.Start();
                var swallower = new K3WarningSwallower();
                var opt = txSym.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(swallower);
                txSym.SetFailureHandlingOptions(opt);

                var existingDupK3 = allWindowSymbols.FirstOrDefault(s => s.Name == "K3_3100x2100");
                if (existingDupK3 == null)
                {
                    symK3 = baseSym.Duplicate("K3_3100x2100") as FamilySymbol;
                    var pW = symK3.get_Parameter(BuiltInParameter.WINDOW_WIDTH);
                    if (pW != null && !pW.IsReadOnly) pW.Set(3.10 * M2FT);
                    var pH = symK3.get_Parameter(BuiltInParameter.WINDOW_HEIGHT);
                    if (pH != null && !pH.IsReadOnly) pH.Set(2.10 * M2FT);
                    var pTM = symK3.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK);
                    if (pTM != null && !pTM.IsReadOnly) pTM.Set("K3");
                }
                else
                {
                    symK3 = existingDupK3;
                }

                if (!symK3.IsActive) symK3.Activate();
                txSym.Commit();
            }

            // 4. Clean previous wall segments on Grid E (Y ~ 14.900) between Trục 2-3 and Trục 9-10 if any
            using (var txClean = new Transaction(doc, "Clean Previous Stair Walls on Grid E"))
            {
                txClean.Start();
                var swallower = new K3WarningSwallower();
                var opt = txClean.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(swallower);
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
                            double xm1 = Math.Min(p1.X, p2.X) * FT2M;
                            double xm2 = Math.Max(p1.X, p2.X) * FT2M;
                            bool nearGridE = Math.Abs(ym1 - 14.900) < 0.10 && Math.Abs(ym2 - 14.900) < 0.10;
                            bool isStairSpan = (xm1 >= 4.0 && xm2 <= 8.5) || (xm1 >= 29.0 && xm2 <= 33.8);
                            return nearGridE && isStairSpan;
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

            // 5. Walls and Windows Definitions along Grid E (Y = 14.900m)
            var wallsDef = new[]
            {
                new { name = "Wall_Stair_Left_GridE",  xStart = 4.350,  xEnd = 8.050,  winX = 6.200,  tag = "K3-1" },
                new { name = "Wall_Stair_Right_GridE", xStart = 29.650, xEnd = 33.350, winX = 31.500, tag = "K3-2" }
            };

            var createdWalls = new List<object>();
            var createdWindows = new List<object>();
            var selectionIds = new List<ElementId>();

            using (var tx = new Transaction(doc, "Create 2 Stair Walls with K3 Windows"))
            {
                tx.Start();
                var swallower = new K3WarningSwallower();
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(swallower);
                tx.SetFailureHandlingOptions(opt);

                double yCenter = 14.900;
                double heightFt = 3.6 * M2FT;
                double sillH = 0.90; // 900mm sill height

                foreach (var wdef in wallsDef)
                {
                    var ptStart = new XYZ(wdef.xStart * M2FT, yCenter * M2FT, 0.0);
                    var ptEnd = new XYZ(wdef.xEnd * M2FT, yCenter * M2FT, 0.0);
                    var line = Line.CreateBound(ptStart, ptEnd);

                    var wall = Wall.Create(doc, line, wallType200.Id, lvlTang1.Id, heightFt, 0.0, false, false);
                    if (lvlTang2 != null)
                    {
                        var topParam = wall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE);
                        if (topParam != null && !topParam.IsReadOnly)
                        {
                            topParam.Set(lvlTang2.Id);
                        }
                    }
                    selectionIds.Add(wall.Id);
                    createdWalls.Add(new
                    {
                        name = wdef.name,
                        id = wall.Id.Value,
                        xStart = wdef.xStart,
                        xEnd = wdef.xEnd,
                        lengthM = wdef.xEnd - wdef.xStart,
                        y = yCenter
                    });

                    // Regenerate so wall geometry exists
                    doc.Regenerate();

                    // Place window K3
                    var winPt = new XYZ(wdef.winX * M2FT, yCenter * M2FT, sillH * M2FT);
                    var winInst = doc.Create.NewFamilyInstance(winPt, symK3, wall, lvlTang1, StructuralType.NonStructural);

                    var markParam = winInst.get_Parameter(BuiltInParameter.ALL_MODEL_MARK);
                    if (markParam != null && !markParam.IsReadOnly)
                    {
                        markParam.Set(wdef.tag);
                    }

                    var sillParam = winInst.get_Parameter(BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM);
                    if (sillParam != null && !sillParam.IsReadOnly)
                    {
                        sillParam.Set(sillH * M2FT);
                    }

                    selectionIds.Add(winInst.Id);
                    createdWindows.Add(new
                    {
                        tag = wdef.tag,
                        id = winInst.Id.Value,
                        symbol = symK3.Name,
                        family = symK3.FamilyName,
                        x = wdef.winX,
                        y = yCenter,
                        widthMm = 3100,
                        heightMm = 2100,
                        sillHeightM = sillH
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
                    var minPt = new XYZ(2.0 * M2FT, 11.0 * M2FT, 0.0);
                    var maxPt = new XYZ(36.0 * M2FT, 17.5 * M2FT, 0.0);
                    uiview?.ZoomAndCenterRectangle(minPt, maxPt);
                }
            }
            catch { }

            // Export high-res detail image
            string outImg = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_stair_walls_k3_result.png";
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
                wallsCount = createdWalls.Count,
                walls = createdWalls,
                windowsCount = createdWindows.Count,
                windows = createdWindows,
                exportedImage = outImg
            };
        }
    }
}
