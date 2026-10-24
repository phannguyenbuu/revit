using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectGlassSymbolicCurves
    {
        private static double ToMm(double ft) => ft * 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var fam = new FilteredElementCollector(doc)
                .OfClass(typeof(Family))
                .Cast<Family>()
                .FirstOrDefault(f => f.Name.Equals("CUA SO 2 CANH NHOM KINH O O THOANG", StringComparison.OrdinalIgnoreCase));

            if (fam == null) return new { error = "Family not found" };

            var famDoc = doc.EditFamily(fam);
            if (famDoc == null) return new { error = "Cannot edit family" };

            var curves = new FilteredElementCollector(famDoc)
                .OfClass(typeof(SymbolicCurve))
                .Cast<SymbolicCurve>()
                .Where(c => c.LineStyle != null && c.LineStyle.Name.Equals("Glass", StringComparison.OrdinalIgnoreCase))
                .Select(c =>
                {
                    var gc = c.GeometryCurve;
                    var p0 = gc.GetEndPoint(0);
                    var p1 = gc.GetEndPoint(1);
                    return new
                    {
                        id = c.Id.Value,
                        p0 = new { x = Math.Round(ToMm(p0.X), 1), y = Math.Round(ToMm(p0.Y), 1), z = Math.Round(ToMm(p0.Z), 1) },
                        p1 = new { x = Math.Round(ToMm(p1.X), 1), y = Math.Round(ToMm(p1.Y), 1), z = Math.Round(ToMm(p1.Z), 1) }
                    };
                })
                .ToList();

            famDoc.Close(false);

            return new
            {
                curves
            };
        }
    }
}
