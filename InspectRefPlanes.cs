using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectRefPlanes
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

                var planes = new FilteredElementCollector(famDoc)
                    .OfClass(typeof(ReferencePlane))
                    .Cast<ReferencePlane>()
                    .Select(rp =>
                    {
                        var bubble = rp.BubbleEnd;
                        var free = rp.FreeEnd;
                        return new
                        {
                            name = rp.Name,
                            bubble = new { x = Math.Round(ToMm(bubble.X), 1), y = Math.Round(ToMm(bubble.Y), 1), z = Math.Round(ToMm(bubble.Z), 1) },
                            free = new { x = Math.Round(ToMm(free.X), 1), y = Math.Round(ToMm(free.Y), 1), z = Math.Round(ToMm(free.Z), 1) }
                        };
                    })
                    .ToList();

                famDoc.Close(false);

                return new
                {
                    totalPlanes = planes.Count,
                    planes
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
