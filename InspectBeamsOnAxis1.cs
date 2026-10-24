using System;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectBeamsOnAxis1
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
                .Where(b => {
                    var lc = b.Location as LocationCurve;
                    if (lc == null) return false;
                    var p0 = lc.Curve.GetEndPoint(0) * FT2MM;
                    var p1 = lc.Curve.GetEndPoint(1) * FT2MM;
                    double midX = (p0.X + p1.X) * 0.5;
                    return Math.Abs(midX - 550.0) < 400.0;
                })
                .Select(b => {
                    var lc = (LocationCurve)b.Location;
                    var p0 = lc.Curve.GetEndPoint(0) * FT2MM;
                    var p1 = lc.Curve.GetEndPoint(1) * FT2MM;
                    var bb = b.get_BoundingBox(null);
                    var lvl = doc.GetElement(b.LevelId)?.Name ?? doc.GetElement(b.get_Parameter(BuiltInParameter.INSTANCE_REFERENCE_LEVEL_PARAM)?.AsElementId())?.Name;
                    var pZOff = b.get_Parameter(BuiltInParameter.Z_OFFSET_VALUE)?.AsDouble() * FT2MM;

                    return new {
                        id = b.Id.Value,
                        name = b.Name,
                        sym = b.Symbol.Name,
                        level = lvl,
                        zOff = pZOff,
                        p0 = $"({p0.X:F0}, {p0.Y:F0}, {p0.Z:F0})",
                        p1 = $"({p1.X:F0}, {p1.Y:F0}, {p1.Z:F0})",
                        minZ = bb != null ? bb.Min.Z * FT2MM : 0,
                        maxZ = bb != null ? bb.Max.Z * FT2MM : 0
                    };
                })
                .OrderBy(b => b.minZ)
                .ThenBy(b => b.p0)
                .ToList();

            return new { count = beams.Count, beams };
        }
    }
}
