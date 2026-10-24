using System;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectElem2363716
    {
        private const double FT2MM = 304.8;
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var e = doc.GetElement(new ElementId(2363716L));
            if (e == null) return new { error = "Element 2363716 not found" };

            var fi = e as FamilyInstance;
            var host = fi?.Host;
            var bb = e.get_BoundingBox(null);
            var lp = e.Location as LocationPoint;

            return new {
                id = e.Id.Value,
                name = e.Name,
                cat = e.Category?.Name,
                type = e.GetType().Name,
                host = host != null ? $"{host.Name} (ID {host.Id.Value}, {host.GetType().Name})" : "None",
                point = lp != null ? $"({lp.Point.X * FT2MM:F1}, {lp.Point.Y * FT2MM:F1}, {lp.Point.Z * FT2MM:F1})" : "None",
                min = bb != null ? $"({bb.Min.X * FT2MM:F1}, {bb.Min.Y * FT2MM:F1}, {bb.Min.Z * FT2MM:F1})" : "None",
                max = bb != null ? $"({bb.Max.X * FT2MM:F1}, {bb.Max.Y * FT2MM:F1}, {bb.Max.Z * FT2MM:F1})" : "None"
            };
        }
    }
}
