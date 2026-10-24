using System;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectFacadeWalls
    {
        private const double FT2MM = 304.8;
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            // Find all walls on Axis 1 (X around 400 to 700)
            var walls = new FilteredElementCollector(doc)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .Where(w => {
                    var lc = w.Location as LocationCurve;
                    if (lc == null) return false;
                    var p0 = lc.Curve.GetEndPoint(0) * FT2MM;
                    var p1 = lc.Curve.GetEndPoint(1) * FT2MM;
                    double midX = (p0.X + p1.X) * 0.5;
                    return Math.Abs(midX - 550.0) < 300.0 && Math.Abs(p0.X - p1.X) < 50.0;
                })
                .Select(w => {
                    var bb = w.get_BoundingBox(null);
                    var lc = (LocationCurve)w.Location;
                    var p0 = lc.Curve.GetEndPoint(0) * FT2MM;
                    var p1 = lc.Curve.GetEndPoint(1) * FT2MM;
                    var lvl = doc.GetElement(w.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT)?.AsElementId())?.Name;
                    var topLvl = doc.GetElement(w.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.AsElementId())?.Name ?? "Unconnected";
                    var h = w.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM)?.AsDouble() * FT2MM;
                    var inserts = w.FindInserts(true, true, true, true).Select(id => {
                        var e = doc.GetElement(id);
                        return $"{e?.Name} ({e?.Category?.Name}, ID {id.Value})";
                    }).ToList();

                    return new {
                        id = w.Id.Value,
                        name = w.Name,
                        level = lvl,
                        topLevel = topLvl,
                        heightMm = h,
                        yRange = $"Y:[{Math.Min(p0.Y, p1.Y):F0}..{Math.Max(p0.Y, p1.Y):F0}]",
                        zRange = $"Z:[{(bb != null ? bb.Min.Z * FT2MM : 0):F0}..{(bb != null ? bb.Max.Z * FT2MM : 0):F0}]",
                        inserts
                    };
                })
                .OrderBy(w => w.level)
                .ThenBy(w => w.yRange)
                .ToList();

            return new { count = walls.Count, walls };
        }
    }
}
