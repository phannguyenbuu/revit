using System;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckGridAndWallAxis1
    {
        private const double FT2MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active doc" };

            var grids = new FilteredElementCollector(doc)
                .OfClass(typeof(Grid))
                .Cast<Grid>()
                .Where(g => g.Name == "1" || g.Name == "11" || g.Name == "A" || g.Name == "B" || g.Name == "C")
                .Select(g => {
                    var line = g.Curve as Line;
                    return new {
                        name = g.Name,
                        p0 = line != null ? $"({line.GetEndPoint(0).X * FT2MM:F1}, {line.GetEndPoint(0).Y * FT2MM:F1}, {line.GetEndPoint(0).Z * FT2MM:F1})" : "None",
                        p1 = line != null ? $"({line.GetEndPoint(1).X * FT2MM:F1}, {line.GetEndPoint(1).Y * FT2MM:F1}, {line.GetEndPoint(1).Z * FT2MM:F1})" : "None",
                    };
                })
                .ToList();

            var inst = doc.GetElement(new ElementId(2391783)) as FamilyInstance;
            var bb = inst?.get_BoundingBox(null);
            var lp = inst?.Location as LocationPoint;

            return new {
                grids,
                instPoint = lp != null ? $"({lp.Point.X * FT2MM:F1}, {lp.Point.Y * FT2MM:F1}, {lp.Point.Z * FT2MM:F1})" : "None",
                instMin = bb != null ? $"({bb.Min.X * FT2MM:F1}, {bb.Min.Y * FT2MM:F1}, {bb.Min.Z * FT2MM:F1})" : "None",
                instMax = bb != null ? $"({bb.Max.X * FT2MM:F1}, {bb.Max.Y * FT2MM:F1}, {bb.Max.Z * FT2MM:F1})" : "None"
            };
        }
    }
}
