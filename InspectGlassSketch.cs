using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectGlassSketch
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

            var glassExt = new FilteredElementCollector(famDoc)
                .OfClass(typeof(Extrusion))
                .Cast<Extrusion>()
                .FirstOrDefault(e => e.Subcategory != null && e.Subcategory.Name.Equals("Glass", StringComparison.OrdinalIgnoreCase))
                ?? new FilteredElementCollector(famDoc).OfClass(typeof(Extrusion)).Cast<Extrusion>().FirstOrDefault(e => e.Id.Value == 2371620L);

            var loops = new List<object>();

            if (glassExt != null && glassExt.Sketch != null)
            {
                CurveArrArray profile = glassExt.Sketch.Profile;
                foreach (CurveArray ca in profile)
                {
                    var lines = new List<object>();
                    foreach (Curve c in ca)
                    {
                        var p0 = c.GetEndPoint(0);
                        var p1 = c.GetEndPoint(1);
                        lines.Add(new
                        {
                            p0 = new { x = Math.Round(ToMm(p0.X), 1), y = Math.Round(ToMm(p0.Y), 1), z = Math.Round(ToMm(p0.Z), 1) },
                            p1 = new { x = Math.Round(ToMm(p1.X), 1), y = Math.Round(ToMm(p1.Y), 1), z = Math.Round(ToMm(p1.Z), 1) }
                        });
                    }
                    loops.Add(lines);
                }
            }

            // Also check the two sash frames: 2371525 and 2371550
            var sashes = new List<object>();
            foreach (long sashId in new[] { 2371525L, 2371550L })
            {
                var s = famDoc.GetElement(new ElementId(sashId)) as Extrusion;
                if (s != null && s.Sketch != null)
                {
                    var sashLoops = new List<object>();
                    foreach (CurveArray ca in s.Sketch.Profile)
                    {
                        var lines = new List<object>();
                        foreach (Curve c in ca)
                        {
                            var p0 = c.GetEndPoint(0);
                            var p1 = c.GetEndPoint(1);
                            lines.Add(new
                            {
                                p0 = new { x = Math.Round(ToMm(p0.X), 1), y = Math.Round(ToMm(p0.Y), 1), z = Math.Round(ToMm(p0.Z), 1) },
                                p1 = new { x = Math.Round(ToMm(p1.X), 1), y = Math.Round(ToMm(p1.Y), 1), z = Math.Round(ToMm(p1.Z), 1) }
                            });
                        }
                        sashLoops.Add(lines);
                    }
                    sashes.Add(new { id = sashId, loops = sashLoops });
                }
            }

            famDoc.Close(false);

            return new
            {
                glassExtId = glassExt?.Id.Value,
                glassLoopsCount = loops.Count,
                glassLoops = loops,
                sashes
            };
        }
    }
}
