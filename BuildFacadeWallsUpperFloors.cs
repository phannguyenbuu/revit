using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Structure;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class FacadeWarningSwallower : IFailuresPreprocessor
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

    public static class BuildFacadeWallsUpperFloors
    {
        private const double FT2MM = 304.8;
        private const double MM2FT = 1.0 / 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            // Find levels
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .ToList();

            var lvl1 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 1") || l.Name.Contains("TRET"));
            var lvl2 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 2"));
            var lvl3 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 3"));
            var lvl4 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 4"));

            if (lvl2 == null || lvl3 == null) return new { error = "Levels not found" };

            // Find Wall Type "gach200_xay moi"
            var wallType = new FilteredElementCollector(doc)
                .OfClass(typeof(WallType))
                .Cast<WallType>()
                .FirstOrDefault(wt => wt.Name == "gach200_xay moi")
                ?? new FilteredElementCollector(doc).OfClass(typeof(WallType)).Cast<WallType>().FirstOrDefault(wt => wt.Width > 0.6);

            // Find Window Symbol S1_1500x1800 (ID 2370793)
            var winSym = doc.GetElement(new ElementId(2370793L)) as FamilySymbol
                ?? new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Windows)
                    .WhereElementIsElementType()
                    .Cast<FamilySymbol>()
                    .FirstOrDefault(s => s.Name == "S1_1500x1800");

            if (wallType == null || winSym == null) return new { error = "WallType or WinSymbol not found" };

            var createdWallIds = new List<long>();
            var createdWinIds = new List<long>();

            using (var tx = new Transaction(doc, "Build Facade Walls & Windows Upper Floors"))
            {
                var prep = new FacadeWarningSwallower();
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(prep);
                tx.SetFailureHandlingOptions(opt);

                tx.Start();

                if (!winSym.IsActive) winSym.Activate();

                // 1. Adjust Tầng 1 Wall 2362083 height to 3300mm to fit under beam 220X500
                var wall1 = doc.GetElement(new ElementId(2362083L)) as Wall;
                if (wall1 != null)
                {
                    var pH = wall1.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM);
                    if (pH != null && !pH.IsReadOnly)
                    {
                        pH.Set(3300.0 * MM2FT);
                    }
                }

                // 2. Remove any leftover existing facade walls on Tầng 2, 3, 4 along Axis 1 between Y 2848 and 10352
                var existingWalls = new FilteredElementCollector(doc)
                    .OfClass(typeof(Wall))
                    .Cast<Wall>()
                    .Where(w => {
                        if (w.Id.Value == 2362083L) return false; // keep Tang 1 wall
                        var lc = w.Location as LocationCurve;
                        if (lc == null) return false;
                        var p0 = lc.Curve.GetEndPoint(0) * FT2MM;
                        var p1 = lc.Curve.GetEndPoint(1) * FT2MM;
                        double midX = (p0.X + p1.X) * 0.5;
                        double minY = Math.Min(p0.Y, p1.Y);
                        double maxY = Math.Max(p0.Y, p1.Y);
                        return Math.Abs(midX - 550.0) < 100.0 && maxY > 2840.0 && minY < 10360.0;
                    })
                    .Select(w => w.Id)
                    .ToList();

                if (existingWalls.Count > 0)
                {
                    try { doc.Delete(existingWalls); } catch {}
                }

                // Coordinates for Axis 1 facade segments
                // X = 550 mm
                // Bay 1: Y from 2848 to 5400 (under Beam 220X500, H = 3000 mm)
                // Bay 2: Y from 5400 to 7800 (under Beam 220X350, H = 3150 mm)
                // Bay 3: Y from 7800 to 10352 (under Beam 220X500, H = 3000 mm)
                double X = 550.0 * MM2FT;
                double Y_start = 2848.0 * MM2FT;
                double Y_b1 = 5400.0 * MM2FT;
                double Y_b2 = 7800.0 * MM2FT;
                double Y_end = 10352.0 * MM2FT;

                double h_500 = 3000.0 * MM2FT;
                double h_350 = 3150.0 * MM2FT;

                var floorLevels = new List<Level> { lvl2, lvl3 };

                foreach (var lvl in floorLevels)
                {
                    // Segment 1 (Bay 1)
                    Line line1 = Line.CreateBound(new XYZ(X, Y_start, 0.0), new XYZ(X, Y_b1, 0.0));
                    Wall w1 = Wall.Create(doc, line1, wallType.Id, lvl.Id, h_500, 0.0, false, false);
                    createdWallIds.Add(w1.Id.Value);

                    // Segment 2 (Bay 2)
                    Line line2 = Line.CreateBound(new XYZ(X, Y_b1, 0.0), new XYZ(X, Y_b2, 0.0));
                    Wall w2 = Wall.Create(doc, line2, wallType.Id, lvl.Id, h_350, 0.0, false, false);
                    createdWallIds.Add(w2.Id.Value);

                    // Segment 3 (Bay 3)
                    Line line3 = Line.CreateBound(new XYZ(X, Y_b2, 0.0), new XYZ(X, Y_end, 0.0));
                    Wall w3 = Wall.Create(doc, line3, wallType.Id, lvl.Id, h_500, 0.0, false, false);
                    createdWallIds.Add(w3.Id.Value);

                    // Windows S1
                    // Window 1: Y = 3640 mm on Segment 1
                    double sillFt = 750.0 * MM2FT;
                    var ptWin1 = new XYZ(X, 3640.0 * MM2FT, sillFt);
                    try
                    {
                        var win1 = doc.Create.NewFamilyInstance(ptWin1, winSym, w1, lvl, StructuralType.NonStructural);
                        win1.get_Parameter(BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM)?.Set(sillFt);
                        createdWinIds.Add(win1.Id.Value);
                    }
                    catch {}

                    // Window 2: Y = 9560 mm on Segment 3
                    var ptWin2 = new XYZ(X, 9560.0 * MM2FT, sillFt);
                    try
                    {
                        var win2 = doc.Create.NewFamilyInstance(ptWin2, winSym, w3, lvl, StructuralType.NonStructural);
                        win2.get_Parameter(BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM)?.Set(sillFt);
                        createdWinIds.Add(win2.Id.Value);
                    }
                    catch {}
                }

                // Tầng 4: Central bay (Y from 5400 to 7800) under attic/terrace
                if (lvl4 != null)
                {
                    double h_lvl4 = 2250.0 * MM2FT; // from 11100 to 13350
                    Line line4 = Line.CreateBound(new XYZ(X, Y_b1, 0.0), new XYZ(X, Y_b2, 0.0));
                    Wall w4 = Wall.Create(doc, line4, wallType.Id, lvl4.Id, h_lvl4, 0.0, false, false);
                    createdWallIds.Add(w4.Id.Value);
                }

                tx.Commit();
            }

            // Export verification 3D view
            string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            string path3D = Path.Combine(outDir, "revit_facade_walls_and_windows_upper.png");
            if (File.Exists(path3D)) try { File.Delete(path3D); } catch {}

            try
            {
                var view3D = uidoc.ActiveView as View3D ?? new FilteredElementCollector(doc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate && v.Name.Contains("{3D}"));

                if (view3D != null)
                {
                    uidoc.ActiveView = view3D;
                    var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view3D.Id);
                    uiview?.ZoomToFit();

                    var opt3D = new ImageExportOptions
                    {
                        FilePath = path3D,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.PNG,
                        ShadowViewsFileType = ImageFileType.PNG,
                        ImageResolution = ImageResolution.DPI_150,
                        ExportRange = ExportRange.CurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 2560
                    };
                    doc.ExportImage(opt3D);
                }
            }
            catch {}

            // Save Document
            bool saved = false;
            try
            {
                doc.Save(new SaveOptions());
                saved = true;
            }
            catch {}

            return new {
                success = true,
                createdWallsCount = createdWallIds.Count,
                createdWallIds,
                createdWindowsCount = createdWinIds.Count,
                createdWinIds,
                saved,
                image = path3D
            };
        }
    }
}
