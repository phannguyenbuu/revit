using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ScanAllViewsDimensions
    {
        private const double FT_TO_MM = 304.8;

        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            // Find all Floor Plans
            var views = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .Where(v => !v.IsTemplate && v.ViewType == ViewType.FloorPlan)
                .ToList();

            var viewReports = new List<object>();

            foreach (var v in views)
            {
                var dims = new FilteredElementCollector(doc, v.Id)
                    .OfClass(typeof(Dimension))
                    .Cast<Dimension>()
                    .ToList();

                if (dims.Count == 0) continue;

                var dimList = new List<object>();
                foreach (var d in dims)
                {
                    var segVals = new List<double>();
                    bool hasZero = false;

                    if (d.Segments != null && d.Segments.Size > 0)
                    {
                        foreach (DimensionSegment s in d.Segments)
                        {
                            double mm = s.Value.HasValue ? Math.Round(s.Value.Value * FT_TO_MM, 1) : -1;
                            if (mm == 0.0 || s.ValueString == "0") hasZero = true;
                            segVals.Add(mm);
                        }
                    }
                    else if (d.Value.HasValue)
                    {
                        double mm = Math.Round(d.Value.Value * FT_TO_MM, 1);
                        if (mm == 0.0 || d.ValueString == "0") hasZero = true;
                        segVals.Add(mm);
                    }

                    XYZ origin = XYZ.Zero;
                    XYZ dir = XYZ.Zero;
                    double totalSpan = 0;
                    if (d.Curve is Line line)
                    {
                        origin = line.Origin;
                        dir = line.Direction;
                        totalSpan = segVals.Sum();
                    }

                    // Check if chain is broken in the middle:
                    // 1. Contains zeros in the middle (e.g. [..., 3600, 0, 0, 3600, ...])
                    // 2. Collinear with other dims in the same view (fragmented chain)
                    bool hasZerosInMiddle = false;
                    for (int i = 1; i < segVals.Count - 1; i++)
                    {
                        if (segVals[i] == 0.0) hasZerosInMiddle = true;
                    }

                    dimList.Add(new
                    {
                        id = d.Id.Value,
                        type = d.DimensionType?.Name,
                        numSegs = d.NumberOfSegments,
                        totalSpanMm = Math.Round(totalSpan, 0),
                        hasZero,
                        hasZerosInMiddle,
                        origin = new { x = Math.Round(origin.X * FT_TO_MM, 0), y = Math.Round(origin.Y * FT_TO_MM, 0) },
                        dir = new { x = Math.Round(dir.X, 2), y = Math.Round(dir.Y, 2) },
                        segVals
                    });
                }

                viewReports.Add(new
                {
                    viewId = v.Id.Value,
                    viewName = v.Name,
                    totalDims = dims.Count,
                    dimsWithZero = dimList.Count(x => (bool)((dynamic)x).hasZero),
                    dimsWithZerosInMiddle = dimList.Count(x => (bool)((dynamic)x).hasZerosInMiddle),
                    dims = dimList
                });
            }

            return new { success = true, viewReports };
        }
    }
}
