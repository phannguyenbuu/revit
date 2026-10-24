using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectZone910
    {
        private static double ToM(double ft) => ft * 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument.Document;

            double minX = 29.0 / 0.3048;
            double maxX = 34.0 / 0.3048;
            double minY = 7.0 / 0.3048;
            double maxY = 15.5 / 0.3048;

            var elements = new FilteredElementCollector(doc)
                .WhereElementIsNotElementType()
                .Where(e => {
                    var bb = e.get_BoundingBox(null);
                    if (bb == null) return false;
                    return bb.Max.X >= minX && bb.Min.X <= maxX && bb.Max.Y >= minY && bb.Min.Y <= maxY;
                })
                .Select(e => new {
                    id = e.Id.Value,
                    cat = e.Category?.Name,
                    name = e.Name,
                    type = e.GetType().Name,
                    loc = e.Location is LocationPoint lp ? $"Point({ToM(lp.Point.X):F2}, {ToM(lp.Point.Y):F2})" :
                          e.Location is LocationCurve lc ? $"Curve({ToM(lc.Curve.GetEndPoint(0).X):F2}, {ToM(lc.Curve.GetEndPoint(0).Y):F2}) -> ({ToM(lc.Curve.GetEndPoint(1).X):F2}, {ToM(lc.Curve.GetEndPoint(1).Y):F2})" : "None"
                })
                .ToList();

            var allStairs = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Stairs)
                .WhereElementIsNotElementType()
                .Select(s => new {
                    id = s.Id.Value,
                    name = s.Name
                })
                .ToList();

            return new { elementsCount = elements.Count, elements, allStairs };
        }
    }
}
