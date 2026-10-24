using System;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectCreatedCubicle
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var insts = new FilteredElementCollector(doc)
                .OfClass(typeof(FamilyInstance))
                .Cast<FamilyInstance>()
                .Where(fi => fi.Symbol?.Family?.Name == "Xi_Xom")
                .Select(fi => {
                    var lp = (fi.Location as LocationPoint)?.Point;
                    return new {
                        id = fi.Id.Value,
                        symbol = fi.Symbol.Name,
                        pt = lp != null ? $"[{lp.X*304.8:F1}, {lp.Y*304.8:F1}, {lp.Z*304.8:F1}]" : "none",
                        rotDeg = (fi.Location as LocationPoint)?.Rotation * 180.0 / Math.PI
                    };
                })
                .ToList();

            long[] wallIds = new long[] { 2405970, 2405971 };
            var walls = wallIds.Select(id => doc.GetElement(new ElementId(id)) as Wall)
                .Where(w => w != null)
                .Select(w => {
                    var lc = w.Location as LocationCurve;
                    var p0 = lc?.Curve.GetEndPoint(0) * 304.8;
                    var p1 = lc?.Curve.GetEndPoint(1) * 304.8;
                    return new {
                        id = w.Id.Value,
                        type = w.WallType.Name,
                        curve = $"[{p0?.X:F0}, {p0?.Y:F0}] -> [{p1?.X:F0}, {p1?.Y:F0}]"
                    };
                })
                .ToList();

            return new {
                xixomInstances = insts,
                walls = walls
            };
        }
    }
}
