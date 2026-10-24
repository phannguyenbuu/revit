using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectTumWalls
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "no doc" };

            var v = doc.GetElement(new ElementId(2370740L)) as ViewPlan;
            if (v == null) return new { error = "no view" };

            var walls = new FilteredElementCollector(doc, v.Id)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .Select(w => {
                    var c = (w.Location as LocationCurve)?.Curve;
                    var p0 = c != null ? c.GetEndPoint(0) : XYZ.Zero;
                    var p1 = c != null ? c.GetEndPoint(1) : XYZ.Zero;
                    return new {
                        id = w.Id.Value,
                        x0 = p0.X * 304.8,
                        y0 = p0.Y * 304.8,
                        x1 = p1.X * 304.8,
                        y1 = p1.Y * 304.8
                    };
                })
                .ToList();

            return new { count = walls.Count, walls };
        }
    }
}
