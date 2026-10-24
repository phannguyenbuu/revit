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
    public class D1WarningSwallower : IFailuresPreprocessor
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

    public static class CreateWallAndD1
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active Revit doc" };

            // 1. Levels
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .ToList();
            var lvlTang1 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));
            var lvlTang2 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 2", StringComparison.OrdinalIgnoreCase));
            if (lvlTang1 == null) return new { error = "Level TẦNG 1 not found" };
            double heightFt = (lvlTang2 != null) ? (lvlTang2.Elevation - lvlTang1.Elevation) : (3.60 * M2FT);

            // 2. Wall Type: gach200_xay moi
            var wallTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(WallType))
                .Cast<WallType>()
                .ToList();
            var wt200 = wallTypes.FirstOrDefault(w => w.Name.Equals("gach200_xay moi", StringComparison.OrdinalIgnoreCase))
                     ?? wallTypes.FirstOrDefault(w => w.Name.Contains("200") && !w.Name.Contains("SENO", StringComparison.OrdinalIgnoreCase));
            if (wt200 == null) return new { error = "WallType gach200_xay moi not found" };

            // 3. Door Symbol: cua thuy luc 2 canh - Đ1
            var doorSym = doc.GetElement(new ElementId(104895L)) as FamilySymbol;
            if (doorSym == null)
            {
                var doorSymbols = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Doors)
                    .WhereElementIsElementType()
                    .Cast<FamilySymbol>()
                    .ToList();
                doorSym = doorSymbols.FirstOrDefault(s => s.FamilyName.Contains("thuy luc", StringComparison.OrdinalIgnoreCase))
                       ?? doorSymbols.FirstOrDefault(s => s.Name.Equals("Đ1", StringComparison.OrdinalIgnoreCase) || s.Name.Equals("D1", StringComparison.OrdinalIgnoreCase));
            }
            if (doorSym == null) return new { error = "Door symbol D1 not found" };

            ElementId createdWallId = ElementId.InvalidElementId;
            ElementId createdDoorId = ElementId.InvalidElementId;
            var placedDoorParams = new List<object>();

            using (var tx = new Transaction(doc, "Create Wall and Door D1"))
            {
                var opts = tx.GetFailureHandlingOptions();
                opts.SetFailuresPreprocessor(new D1WarningSwallower());
                tx.SetFailureHandlingOptions(opts);

                tx.Start();

                if (!doorSym.IsActive)
                {
                    doorSym.Activate();
                    doc.Regenerate();
                }

                // Delete any existing wall along this exact segment to allow clean idempotency
                var existingWalls = new FilteredElementCollector(doc)
                    .OfClass(typeof(Wall))
                    .Cast<Wall>()
                    .Where(w =>
                    {
                        if (w.Location is LocationCurve lc)
                        {
                            var p0 = lc.Curve.GetEndPoint(0);
                            var p1 = lc.Curve.GetEndPoint(1);
                            double x0 = p0.X * 0.3048, y0 = p0.Y * 0.3048;
                            double x1 = p1.X * 0.3048, y1 = p1.Y * 0.3048;
                            if (Math.Abs(x0 - 0.55) < 0.15 && Math.Abs(x1 - 0.55) < 0.15)
                            {
                                double minY = Math.Min(y0, y1);
                                double maxY = Math.Max(y0, y1);
                                if (minY >= 4.0 && maxY <= 9.2) return true;
                            }
                        }
                        return false;
                    })
                    .ToList();

                foreach (var ew in existingWalls)
                {
                    try { doc.Delete(ew.Id); } catch { }
                }

                // Create Wall: (0.550, 4.200) to (0.550, 9.000)
                var pStart = new XYZ(0.550 * M2FT, 4.200 * M2FT, lvlTang1.Elevation);
                var pEnd = new XYZ(0.550 * M2FT, 9.000 * M2FT, lvlTang1.Elevation);
                var wallLine = Line.CreateBound(pStart, pEnd);

                var newWall = Wall.Create(doc, wallLine, wt200.Id, lvlTang1.Id, heightFt, 0, false, false);
                createdWallId = newWall.Id;

                doc.Regenerate();

                // Place Door D1 at center (0.550, 6.600)
                var doorLoc = new XYZ(0.550 * M2FT, 6.600 * M2FT, lvlTang1.Elevation);
                var newDoor = doc.Create.NewFamilyInstance(doorLoc, doorSym, newWall, lvlTang1, StructuralType.NonStructural);
                createdDoorId = newDoor.Id;

                doc.Regenerate();

                // Check instance parameters of placed door
                foreach (Parameter p in newDoor.Parameters)
                {
                    if (p.Definition.Name.Contains("Width") || p.Definition.Name.Contains("Height") ||
                        p.Definition.Name.Contains("Rộng") || p.Definition.Name.Contains("Cao") ||
                        p.Definition.Name.Contains("b") || p.Definition.Name.Contains("h") ||
                        p.Definition.Name.Contains("Size"))
                    {
                        placedDoorParams.Add(new { name = p.Definition.Name, valStr = p.AsValueString(), valDbl = p.StorageType == StorageType.Double ? p.AsDouble() * 304.8 : 0 });
                    }
                }

                tx.Commit();
            }

            // Export verification image focused on D1 zone
            string outImgPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_d1_result.png";
            string cleanImgPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_d1_clean.png";

            try
            {
                if (File.Exists(outImgPath)) File.Delete(outImgPath);
                if (File.Exists(cleanImgPath)) File.Delete(cleanImgPath);

                var selIds = new List<ElementId>();
                if (createdWallId != ElementId.InvalidElementId) selIds.Add(createdWallId);
                if (createdDoorId != ElementId.InvalidElementId) selIds.Add(createdDoorId);
                uidoc.Selection.SetElementIds(selIds);

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

                // Clean export without selection
                uidoc.Selection.SetElementIds(new List<ElementId>());
                var expOptClean = new ImageExportOptions
                {
                    FilePath = cleanImgPath,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_300,
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 3000
                };
                doc.ExportImage(expOptClean);
            }
            catch { }

            return new
            {
                success = true,
                wallId = createdWallId.Value,
                doorId = createdDoorId.Value,
                doorFamily = doorSym.FamilyName,
                doorType = doorSym.Name,
                wallType = wt200.Name,
                doorParams = placedDoorParams,
                highlightImage = outImgPath,
                cleanImage = cleanImgPath
            };
        }
    }
}
