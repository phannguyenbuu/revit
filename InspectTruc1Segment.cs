using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectTruc1Segment
    {
        private static double ToMm(double ft) => ft * 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                // Find all walls near X = 550mm and Y between 11000 and 13300
                var walls = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Walls)
                    .WhereElementIsNotElementType()
                    .Cast<Wall>()
                    .Where(w =>
                    {
                        var bb = w.get_BoundingBox(null);
                        if (bb == null) return false;
                        double minX = ToMm(bb.Min.X);
                        double maxX = ToMm(bb.Max.X);
                        double minY = ToMm(bb.Min.Y);
                        double maxY = ToMm(bb.Max.Y);
                        return minX <= 1000 && maxX >= 100 && maxY >= 12000 && minY <= 13000;
                    })
                    .Select(w =>
                    {
                        var locCurve = (w.Location as LocationCurve)?.Curve;
                        var p0 = locCurve != null ? locCurve.GetEndPoint(0) : null;
                        var p1 = locCurve != null ? locCurve.GetEndPoint(1) : null;
                        var bb = w.get_BoundingBox(null);
                        return new
                        {
                            id = w.Id.Value,
                            typeName = w.WallType.Name,
                            level = doc.GetElement(w.LevelId)?.Name,
                            p0 = p0 != null ? new { x = Math.Round(ToMm(p0.X), 1), y = Math.Round(ToMm(p0.Y), 1), z = Math.Round(ToMm(p0.Z), 1) } : null,
                            p1 = p1 != null ? new { x = Math.Round(ToMm(p1.X), 1), y = Math.Round(ToMm(p1.Y), 1), z = Math.Round(ToMm(p1.Z), 1) } : null,
                            bbZ = bb != null ? new { minZ = Math.Round(ToMm(bb.Min.Z), 1), maxZ = Math.Round(ToMm(bb.Max.Z), 1) } : null
                        };
                    })
                    .ToList();

                return new { walls };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
