using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class FindTumRoofHost
    {
        private const double FT2M = 0.3048;
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var allLevels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .OrderBy(l => l.Elevation)
                .Select(l => new { id = l.Id.Value, name = l.Name, elevM = Math.Round(l.Elevation * FT2M, 3) })
                .ToList();

            // Find all walls on Tum or higher
            var walls = new FilteredElementCollector(doc)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .Where(w => {
                    var l = doc.GetElement(w.LevelId) as Level;
                    return (l?.Elevation ?? 0) * FT2M >= 10.0;
                })
                .Select(w => {
                    var l = doc.GetElement(w.LevelId) as Level;
                    var lc = w.Location as LocationCurve;
                    var p0 = lc?.Curve.GetEndPoint(0);
                    var p1 = lc?.Curve.GetEndPoint(1);
                    return new {
                        id = w.Id.Value,
                        level = l?.Name,
                        elevM = (l?.Elevation ?? 0) * FT2M,
                        p0 = p0 != null ? new { x = Math.Round(p0.X * FT2M * 1000, 1), y = Math.Round(p0.Y * FT2M * 1000, 1) } : null,
                        p1 = p1 != null ? new { x = Math.Round(p1.X * FT2M * 1000, 1), y = Math.Round(p1.Y * FT2M * 1000, 1) } : null
                    };
                })
                .ToList();

            // Find all columns on Tum or higher
            var cols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Columns)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Where(c => {
                    var l = doc.GetElement(c.LevelId) as Level;
                    return (l?.Elevation ?? 0) * FT2M >= 10.0;
                })
                .Select(c => {
                    var l = doc.GetElement(c.LevelId) as Level;
                    var lp = c.Location as LocationPoint;
                    var p = lp?.Point;
                    return new {
                        id = c.Id.Value,
                        level = l?.Name,
                        p = p != null ? new { x = Math.Round(p.X * FT2M * 1000, 1), y = Math.Round(p.Y * FT2M * 1000, 1) } : null
                    };
                })
                .ToList();

            // Also check structural columns
            var structCols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Where(c => {
                    var l = doc.GetElement(c.LevelId) as Level;
                    return (l?.Elevation ?? 0) * FT2M >= 10.0;
                })
                .Select(c => {
                    var l = doc.GetElement(c.LevelId) as Level;
                    var lp = c.Location as LocationPoint;
                    var p = lp?.Point;
                    return new {
                        id = c.Id.Value,
                        level = l?.Name,
                        p = p != null ? new { x = Math.Round(p.X * FT2M * 1000, 1), y = Math.Round(p.Y * FT2M * 1000, 1) } : null
                    };
                })
                .ToList();

            // Grids in project
            var grids = new FilteredElementCollector(doc)
                .OfClass(typeof(Grid))
                .Cast<Grid>()
                .Select(g => {
                    var c = g.Curve;
                    var p0 = c.GetEndPoint(0);
                    var p1 = c.GetEndPoint(1);
                    return new {
                        name = g.Name,
                        p0 = new { x = Math.Round(p0.X * FT2M * 1000, 1), y = Math.Round(p0.Y * FT2M * 1000, 1) },
                        p1 = new { x = Math.Round(p1.X * FT2M * 1000, 1), y = Math.Round(p1.Y * FT2M * 1000, 1) }
                    };
                })
                .ToList();

            return new { allLevels, walls, cols, structCols, grids };
        }
    }
}
