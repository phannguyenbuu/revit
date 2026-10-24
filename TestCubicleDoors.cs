using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestCubicleDoors
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            // Find all walls and plumbing in X in [35000, 38000], Y in [10000, 14000]
            var walls = new FilteredElementCollector(doc)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .Where(w => {
                    var bbox = w.get_BoundingBox(null);
                    if (bbox == null) return false;
                    double xMid = (bbox.Min.X + bbox.Max.X) * 0.5 * 304.8;
                    double yMid = (bbox.Min.Y + bbox.Max.Y) * 0.5 * 304.8;
                    return xMid >= 34000 && xMid <= 38000 && yMid >= 10500 && yMid <= 13500;
                })
                .Select(w => new {
                    id = w.Id.Value,
                    name = w.Name,
                    type = w.WallType.Name,
                    length = (w.Location as LocationCurve)?.Curve.Length * 304.8
                })
                .ToList();

            var plumbing = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_PlumbingFixtures)
                .OfClass(typeof(FamilyInstance))
                .Cast<FamilyInstance>()
                .Where(fi => {
                    var pt = (fi.Location as LocationPoint)?.Point;
                    if (pt == null) return false;
                    double x = pt.X * 304.8;
                    double y = pt.Y * 304.8;
                    return x >= 34000 && x <= 38000 && y >= 10500 && y <= 13500;
                })
                .Select(fi => new {
                    id = fi.Id.Value,
                    family = fi.Symbol.FamilyName,
                    symbol = fi.Symbol.Name,
                    pt = $"[{(fi.Location as LocationPoint).Point.X * 304.8:F1}, {(fi.Location as LocationPoint).Point.Y * 304.8:F1}]"
                })
                .ToList();

            return new { walls, plumbing };
        }
    }
}
