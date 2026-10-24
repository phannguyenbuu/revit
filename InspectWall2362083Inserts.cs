using System;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectWall2362083Inserts
    {
        private const double FT2MM = 304.8;
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var wall = doc.GetElement(new ElementId(2362083L)) as Wall;
            if (wall == null) return new { error = "Wall 2362083 not found" };

            var lc = (LocationCurve)wall.Location;
            var p0 = lc.Curve.GetEndPoint(0) * FT2MM;
            var p1 = lc.Curve.GetEndPoint(1) * FT2MM;
            var bb = wall.get_BoundingBox(null);

            var inserts = wall.FindInserts(true, true, true, true);
            var insertList = new List<object>();

            foreach (var insId in inserts)
            {
                var e = doc.GetElement(insId) as FamilyInstance;
                if (e == null) continue;

                var ibb = e.get_BoundingBox(null);
                var lp = e.Location as LocationPoint;
                var pt = lp?.Point;
                var sill = e.get_Parameter(BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM)?.AsDouble() * FT2MM;

                insertList.Add(new {
                    id = insId.Value,
                    name = e.Name,
                    sym = e.Symbol.Name,
                    cat = e.Category.Name,
                    sillMm = sill,
                    point = pt != null ? $"({pt.X * FT2MM:F1}, {pt.Y * FT2MM:F1}, {pt.Z * FT2MM:F1})" : "None",
                    minZ = ibb != null ? ibb.Min.Z * FT2MM : 0,
                    maxZ = ibb != null ? ibb.Max.Z * FT2MM : 0,
                    minY = ibb != null ? ibb.Min.Y * FT2MM : 0,
                    maxY = ibb != null ? ibb.Max.Y * FT2MM : 0
                });
            }

            return new {
                wallId = wall.Id.Value,
                p0 = $"({p0.X:F1}, {p0.Y:F1}, {p0.Z:F1})",
                p1 = $"({p1.X:F1}, {p1.Y:F1}, {p1.Z:F1})",
                h = wall.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM)?.AsDouble() * FT2MM,
                inserts = insertList
            };
        }
    }
}
