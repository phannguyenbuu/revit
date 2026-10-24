using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectRevitTruc1
    {
        private static double ToMm(double ft) => ft * 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                // Find all walls near X = 550mm (0.55m) and Y between 10m and 15m
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
                        return minX <= 1500 && maxX >= -500 && maxY >= 10000 && minY <= 15000;
                    })
                    .Select(w =>
                    {
                        var bb = w.get_BoundingBox(null);
                        var locCurve = (w.Location as LocationCurve)?.Curve;
                        var p0 = locCurve != null ? locCurve.GetEndPoint(0) : null;
                        var p1 = locCurve != null ? locCurve.GetEndPoint(1) : null;
                        return new
                        {
                            id = w.Id.Value,
                            name = w.Name,
                            typeName = w.WallType.Name,
                            level = doc.GetElement(w.LevelId)?.Name,
                            p0 = p0 != null ? new { x = Math.Round(ToMm(p0.X), 1), y = Math.Round(ToMm(p0.Y), 1), z = Math.Round(ToMm(p0.Z), 1) } : null,
                            p1 = p1 != null ? new { x = Math.Round(ToMm(p1.X), 1), y = Math.Round(ToMm(p1.Y), 1), z = Math.Round(ToMm(p1.Z), 1) } : null,
                            bb = bb != null ? new
                            {
                                min = new { x = Math.Round(ToMm(bb.Min.X), 0), y = Math.Round(ToMm(bb.Min.Y), 0), z = Math.Round(ToMm(bb.Min.Z), 0) },
                                max = new { x = Math.Round(ToMm(bb.Max.X), 0), y = Math.Round(ToMm(bb.Max.Y), 0), z = Math.Round(ToMm(bb.Max.Z), 0) }
                            } : null
                        };
                    })
                    .ToList();

                // Find all windows near X = 550mm
                var windows = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Windows)
                    .WhereElementIsNotElementType()
                    .Cast<FamilyInstance>()
                    .Where(w =>
                    {
                        var bb = w.get_BoundingBox(null);
                        if (bb == null) return false;
                        double minX = ToMm(bb.Min.X);
                        double maxX = ToMm(bb.Max.X);
                        return minX <= 1500 && maxX >= -500;
                    })
                    .Select(w =>
                    {
                        var bb = w.get_BoundingBox(null);
                        return new
                        {
                            id = w.Id.Value,
                            fam = w.Symbol.FamilyName,
                            type = w.Symbol.Name,
                            level = doc.GetElement(w.LevelId)?.Name,
                            bb = bb != null ? new
                            {
                                min = new { x = Math.Round(ToMm(bb.Min.X), 0), y = Math.Round(ToMm(bb.Min.Y), 0), z = Math.Round(ToMm(bb.Min.Z), 0) },
                                max = new { x = Math.Round(ToMm(bb.Max.X), 0), y = Math.Round(ToMm(bb.Max.Y), 0), z = Math.Round(ToMm(bb.Max.Z), 0) }
                            } : null
                        };
                    })
                    .ToList();

                return new { walls, windows };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
