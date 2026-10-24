using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CompareTwoGlassDoors
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var wall = doc.GetElement(new ElementId(2362083L)) as Wall;
            if (wall == null) return new { error = "Wall 2362083 not found" };

            var levels = new FilteredElementCollector(doc).OfClass(typeof(Level)).Cast<Level>().ToList();
            var lvlTang1 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));
            var lvlTang2 = levels.FirstOrDefault(l => l.Name.Contains("TẦNG 2", StringComparison.OrdinalIgnoreCase));

            double z0 = lvlTang1.Elevation;
            double z1 = z0 + (2.70 * 3.2808398950131235); // 2.7m opening height

            // Opening from Y = 5.65m to Y = 7.55m at X = 0.55m
            double m2ft = 3.2808398950131235;
            var p0 = new XYZ(0.550 * m2ft, 5.650 * m2ft, z0);
            var p1 = new XYZ(0.550 * m2ft, 7.550 * m2ft, z1);

            Opening opening = null;
            string opError = null;
            using (var tx = new Transaction(doc, "Test Wall Opening"))
            {
                tx.Start();
                try
                {
                    opening = doc.Create.NewOpening(wall, p0, p1);
                    doc.Regenerate();
                    tx.Commit();
                }
                catch (Exception ex)
                {
                    opError = ex.Message;
                    tx.RollBack();
                }
            }

            return new
            {
                success = opening != null,
                openingId = opening?.Id.Value,
                error = opError
            };
        }
    }
}
