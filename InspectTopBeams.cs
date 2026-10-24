using System;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectTopBeams
    {
        private const double FT2MM = 304.8;
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var beams = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralFraming)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Select(b => {
                    var lc = b.Location as LocationCurve;
                    if (lc == null) return null;
                    var p0 = lc.Curve.GetEndPoint(0) * FT2MM;
                    var p1 = lc.Curve.GetEndPoint(1) * FT2MM;
                    var bb = b.get_BoundingBox(null);
                    return new {
                        id = b.Id.Value,
                        sym = b.Symbol.Name,
                        p0 = $"({p0.X:F0}, {p0.Y:F0}, {p0.Z:F0})",
                        p1 = $"({p1.X:F0}, {p1.Y:F0}, {p1.Z:F0})",
                        minX = Math.Min(p0.X, p1.X),
                        maxX = Math.Max(p0.X, p1.X),
                        minY = Math.Min(p0.Y, p1.Y),
                        maxY = Math.Max(p0.Y, p1.Y),
                        minZ = bb != null ? bb.Min.Z * FT2MM : 0,
                        maxZ = bb != null ? bb.Max.Z * FT2MM : 0
                    };
                })
                .Where(b => b != null && b.minZ > 12000.0)
                .OrderBy(b => b.minZ)
                .ToList();

            return new { count = beams.Count, beams };
        }
    }
}
