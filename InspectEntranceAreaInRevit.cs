using System;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectEntranceAreaInRevit
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument.Document;

            // Find all walls near (0,0) or X in [-5, 10], Y in [-5, 10]
            var walls = new FilteredElementCollector(doc)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .Where(w =>
                {
                    var bb = w.get_BoundingBox(null);
                    if (bb == null) return false;
                    return bb.Min.X * FT2M >= -5 && bb.Max.X * FT2M <= 10 && bb.Min.Y * FT2M >= -5 && bb.Max.Y * FT2M <= 10;
                })
                .Select(w => new
                {
                    id = w.Id.Value,
                    name = w.Name,
                    type = w.WallType.Name,
                    bbMin = new { x = Math.Round(w.get_BoundingBox(null).Min.X * FT2M, 2), y = Math.Round(w.get_BoundingBox(null).Min.Y * FT2M, 2), z = Math.Round(w.get_BoundingBox(null).Min.Z * FT2M, 2) },
                    bbMax = new { x = Math.Round(w.get_BoundingBox(null).Max.X * FT2M, 2), y = Math.Round(w.get_BoundingBox(null).Max.Y * FT2M, 2), z = Math.Round(w.get_BoundingBox(null).Max.Z * FT2M, 2) }
                })
                .ToList();

            var cols = new FilteredElementCollector(doc)
                .OfClass(typeof(FamilyInstance))
                .OfCategory(BuiltInCategory.OST_Columns)
                .Cast<FamilyInstance>()
                .Concat(new FilteredElementCollector(doc).OfClass(typeof(FamilyInstance)).OfCategory(BuiltInCategory.OST_StructuralColumns).Cast<FamilyInstance>())
                .Where(c =>
                {
                    var bb = c.get_BoundingBox(null);
                    if (bb == null) return false;
                    return bb.Min.X * FT2M >= -5 && bb.Max.X * FT2M <= 10 && bb.Min.Y * FT2M >= -5 && bb.Max.Y * FT2M <= 10;
                })
                .Select(c => new
                {
                    id = c.Id.Value,
                    name = c.Name,
                    loc = c.Location is LocationPoint lp ? new { x = Math.Round(lp.Point.X * FT2M, 2), y = Math.Round(lp.Point.Y * FT2M, 2), z = Math.Round(lp.Point.Z * FT2M, 2) } : null
                })
                .ToList();

            return new { walls, cols };
        }
    }
}
