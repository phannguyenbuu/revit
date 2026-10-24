using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectSashProfile
    {
        private static double ToMm(double ft) => ft * 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
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

                var extrusions = new FilteredElementCollector(famDoc)
                    .OfClass(typeof(Extrusion))
                    .Cast<Extrusion>()
                    .ToList();

                var results = new List<object>();

                foreach (var ext in extrusions)
                {
                    var bb = ext.get_BoundingBox(null);
                    var sketch = ext.Sketch;
                    int loopCount = 0;
                    var loopDetails = new List<object>();

                    if (sketch != null)
                    {
                        CurveArrArray profile = sketch.Profile;
                        loopCount = profile.Size;

                        foreach (CurveArray ca in profile)
                        {
                            var curves = new List<object>();
                            double minZ = double.MaxValue, maxZ = double.MinValue;
                            double minX = double.MaxValue, maxX = double.MinValue;

                            foreach (Curve c in ca)
                            {
                                var p0 = c.GetEndPoint(0);
                                var p1 = c.GetEndPoint(1);
                                double x0 = ToMm(p0.X), z0 = ToMm(p0.Z);
                                double x1 = ToMm(p1.X), z1 = ToMm(p1.Z);

                                minX = Math.Min(minX, Math.Min(x0, x1));
                                maxX = Math.Max(maxX, Math.Max(x0, x1));
                                minZ = Math.Min(minZ, Math.Min(z0, z1));
                                maxZ = Math.Max(maxZ, Math.Max(z0, z1));

                                curves.Add(new { x0 = Math.Round(x0, 1), z0 = Math.Round(z0, 1), x1 = Math.Round(x1, 1), z1 = Math.Round(z1, 1) });
                            }

                            loopDetails.Add(new
                            {
                                bounds = $"X: [{minX:F1}, {maxX:F1}], Z: [{minZ:F1}, {maxZ:F1}] (w={maxX-minX:F1}, h={maxZ-minZ:F1})",
                                curveCount = ca.Size,
                                curves
                            });
                        }
                    }

                    results.Add(new
                    {
                        id = ext.Id.Value,
                        subCat = ext.Subcategory?.Name ?? "None",
                        bb = bb != null ? $"dx={ToMm(bb.Max.X - bb.Min.X):F0}, dy={ToMm(bb.Max.Y - bb.Min.Y):F0}, dz={ToMm(bb.Max.Z - bb.Min.Z):F0}" : "no bb",
                        loopCount,
                        loops = loopDetails
                    });
                }

                famDoc.Close(false);

                return new
                {
                    success = true,
                    extrusions = results
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
