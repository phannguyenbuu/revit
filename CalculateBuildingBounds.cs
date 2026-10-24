using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CalculateBuildingBounds
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var v1 = doc.GetElement(new ElementId(312L)) as View;
            if (v1 == null) return new { error = "No view 312" };

            var cats = new List<BuiltInCategory>
            {
                BuiltInCategory.OST_Walls,
                BuiltInCategory.OST_Grids,
                BuiltInCategory.OST_Dimensions,
                BuiltInCategory.OST_Doors,
                BuiltInCategory.OST_Windows,
                BuiltInCategory.OST_Floors,
                BuiltInCategory.OST_Stairs
            };

            var boundsByCat = new Dictionary<string, object>();
            double overallMinX = double.MaxValue, overallMinY = double.MaxValue;
            double overallMaxX = double.MinValue, overallMaxY = double.MinValue;

            foreach (var bic in cats)
            {
                var elements = new FilteredElementCollector(doc, v1.Id)
                    .OfCategory(bic)
                    .WhereElementIsNotElementType()
                    .ToList();

                double minX = double.MaxValue, minY = double.MaxValue;
                double maxX = double.MinValue, maxY = double.MinValue;
                int c = 0;

                foreach (var e in elements)
                {
                    var bb = e.get_BoundingBox(v1);
                    if (bb != null)
                    {
                        double x1 = bb.Min.X * 304.8;
                        double y1 = bb.Min.Y * 304.8;
                        double x2 = bb.Max.X * 304.8;
                        double y2 = bb.Max.Y * 304.8;

                        // exclude infinite grids if any
                        if (bic == BuiltInCategory.OST_Grids)
                        {
                            // keep within reasonable limits
                            if (Math.Abs(x1) > 200000 || Math.Abs(x2) > 200000) continue;
                            if (Math.Abs(y1) > 200000 || Math.Abs(y2) > 200000) continue;
                        }

                        minX = Math.Min(minX, Math.Min(x1, x2));
                        minY = Math.Min(minY, Math.Min(y1, y2));
                        maxX = Math.Max(maxX, Math.Max(x1, x2));
                        maxY = Math.Max(maxY, Math.Max(y1, y2));
                        c++;
                    }
                }

                if (c > 0)
                {
                    boundsByCat[bic.ToString()] = new { count = c, minX, minY, maxX, maxY };
                    if (bic != BuiltInCategory.OST_Grids) // grids might extend far
                    {
                        overallMinX = Math.Min(overallMinX, minX);
                        overallMinY = Math.Min(overallMinY, minY);
                        overallMaxX = Math.Max(overallMaxX, maxX);
                        overallMaxY = Math.Max(overallMaxY, maxY);
                    }
                }
            }

            return new
            {
                success = true,
                boundsByCat,
                overallNonGrid = new { overallMinX, overallMinY, overallMaxX, overallMaxY }
            };
        }
    }
}
