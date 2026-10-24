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
    public static class TestPlaceD1Wall
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active Revit doc" };

            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .ToList();
            var lvlTang1 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));
            var lvlTang2 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 2", StringComparison.OrdinalIgnoreCase));
            if (lvlTang1 == null) return new { error = "Level TẦNG 1 not found" };
            double heightFt = (lvlTang2 != null) ? (lvlTang2.Elevation - lvlTang1.Elevation) : (3.60 * M2FT);

            // Wall type
            var wallTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(WallType))
                .Cast<WallType>()
                .ToList();
            var wt200 = wallTypes.FirstOrDefault(w => w.Name.Equals("gach200_xay moi", StringComparison.OrdinalIgnoreCase))
                     ?? wallTypes.FirstOrDefault(w => w.Name.Contains("200") && !w.Name.Contains("SENO", StringComparison.OrdinalIgnoreCase));
            if (wt200 == null) return new { error = "WallType gach200_xay moi not found" };

            // Door symbol: Type 138400 (CUA ĐI 4 CANH CO O THOANG - D1)
            var doorSym = doc.GetElement(new ElementId(138400L)) as FamilySymbol;
            if (doorSym == null) return new { error = "Symbol 138400 not found" };

            ElementId wallId = ElementId.InvalidElementId;
            ElementId doorId = ElementId.InvalidElementId;

            using (var tx = new Transaction(doc, "Test Place D1 Wall"))
            {
                var opts = tx.GetFailureHandlingOptions();
                opts.SetFailuresPreprocessor(new D1WarningSwallower());
                tx.SetFailureHandlingOptions(opts);

                tx.Start();

                // Delete previous test door
                try { doc.Delete(new ElementId(2362082L)); } catch { }

                // Delete any walls along Axis 1 between Y = 4.0 and 9.2
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

                if (!doorSym.IsActive) doorSym.Activate();

                // Create wall: (0.550, 4.200) to (0.550, 9.000)
                var pStart = new XYZ(0.550 * M2FT, 4.200 * M2FT, lvlTang1.Elevation);
                var pEnd = new XYZ(0.550 * M2FT, 9.000 * M2FT, lvlTang1.Elevation);
                var wallLine = Line.CreateBound(pStart, pEnd);
                var wall = Wall.Create(doc, wallLine, wt200.Id, lvlTang1.Id, heightFt, 0, false, false);
                wallId = wall.Id;

                doc.Regenerate();

                // Place door at (0.550, 6.600)
                var doorLoc = new XYZ(0.550 * M2FT, 6.600 * M2FT, lvlTang1.Elevation);
                var door = doc.Create.NewFamilyInstance(doorLoc, doorSym, wall, lvlTang1, StructuralType.NonStructural);
                doorId = door.Id;

                doc.Regenerate();
                tx.Commit();
            }

            // Export test image
            string imgPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\test_d1_4canh.png";
            try
            {
                if (File.Exists(imgPath)) File.Delete(imgPath);
                var expOpt = new ImageExportOptions
                {
                    FilePath = imgPath,
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

            return new { success = true, wallId = wallId.Value, doorId = doorId.Value, image = imgPath };
        }
    }
}
