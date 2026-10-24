using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectExtrusionBounds
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var app = uiapp.Application;
            string rfaPath = @"D:\Dropbox\_Documents\RevitAI\Concrete-Rectangular-Column.rfa";
            var famDoc = app.OpenDocumentFile(rfaPath);
            if (famDoc == null) return new { error = "Cannot open RFA" };

            var ext = new FilteredElementCollector(famDoc)
                .OfClass(typeof(Extrusion))
                .Cast<Extrusion>()
                .FirstOrDefault();

            if (ext == null)
            {
                famDoc.Close(false);
                return new { error = "No extrusion found" };
            }

            var bb = ext.get_BoundingBox(null);
            var min = bb.Min;
            var max = bb.Max;

            // Also check sketch curves
            var profile = ext.Sketch?.Profile;
            var curvesInfo = "";
            if (profile != null)
            {
                foreach (CurveArrArray caa in profile)
                {
                    foreach (CurveArray ca in caa)
                    {
                        foreach (Curve c in ca)
                        {
                            var p0 = c.GetEndPoint(0);
                            var p1 = c.GetEndPoint(1);
                            curvesInfo += $"({p0.X * 304.8:F1}, {p0.Y * 304.8:F1}) -> ({p1.X * 304.8:F1}, {p1.Y * 304.8:F1}); ";
                        }
                    }
                }
            }

            famDoc.Close(false);

            return new
            {
                minMm = new { x = min.X * 304.8, y = min.Y * 304.8, z = min.Z * 304.8 },
                maxMm = new { x = max.X * 304.8, y = max.Y * 304.8, z = max.Z * 304.8 },
                centerMm = new { x = (min.X + max.X) / 2.0 * 304.8, y = (min.Y + max.Y) / 2.0 * 304.8 },
                curves = curvesInfo
            };
        }
    }
}
