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
    public static class TestRotateDoorD1
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
            if (lvlTang1 == null) return new { error = "Level TẦNG 1 not found" };

            var doorSym = doc.GetElement(new ElementId(104895L)) as FamilySymbol;
            if (doorSym == null) return new { error = "Symbol 104895 not found" };

            ElementId doorId = ElementId.InvalidElementId;

            using (var tx = new Transaction(doc, "Test Rotate Door D1"))
            {
                var opts = tx.GetFailureHandlingOptions();
                opts.SetFailuresPreprocessor(new D1WarningSwallower());
                tx.SetFailureHandlingOptions(opts);

                tx.Start();

                // Delete previous test wall and door
                try { doc.Delete(new ElementId(2362080L)); } catch { }
                try { doc.Delete(new ElementId(2362081L)); } catch { }

                if (!doorSym.IsActive) doorSym.Activate();

                // Place door at (0.550, 6.600)
                var pt = new XYZ(0.550 * M2FT, 6.600 * M2FT, lvlTang1.Elevation);
                var door = doc.Create.NewFamilyInstance(pt, doorSym, lvlTang1, StructuralType.NonStructural);
                doorId = door.Id;

                // Rotate by 90 degrees around Z axis at pt
                var axis = Line.CreateBound(pt, pt + XYZ.BasisZ);
                ElementTransformUtils.RotateElement(doc, door.Id, axis, Math.PI / 2.0);

                doc.Regenerate();
                tx.Commit();
            }

            // Export test image
            string imgPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\test_door_rotate.png";
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

            return new { success = true, doorId = doorId.Value, image = imgPath };
        }
    }
}
