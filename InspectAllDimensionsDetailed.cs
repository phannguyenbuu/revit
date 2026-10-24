using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectAllDimensionsDetailed
    {
        private const double FT_TO_MM = 304.8;

        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var viewIds = new List<long> { 312L, 695L, 1727632L, 2409349L };
            var results = new List<object>();

            foreach (var vId in viewIds)
            {
                var v = doc.GetElement(new ElementId(vId)) as View;
                if (v == null) continue;

                var dims = new FilteredElementCollector(doc, v.Id)
                    .OfClass(typeof(Dimension))
                    .Cast<Dimension>()
                    .ToList();

                var dimDetails = new List<object>();

                foreach (var d in dims)
                {
                    var segList = new List<object>();
                    bool hasZero = false;

                    if (d.Segments != null && d.Segments.Size > 0)
                    {
                        int sIdx = 0;
                        foreach (DimensionSegment seg in d.Segments)
                        {
                            double valMm = seg.Value.HasValue ? Math.Round(seg.Value.Value * FT_TO_MM, 1) : -1;
                            string valStr = seg.ValueString ?? "";
                            if (valMm == 0.0 || valStr == "0") hasZero = true;

                            segList.Add(new
                            {
                                index = sIdx++,
                                valMm,
                                valStr,
                                text = seg.ValueOverride ?? "",
                                above = seg.Above ?? "",
                                below = seg.Below ?? ""
                            });
                        }
                    }
                    else
                    {
                        double valMm = d.Value.HasValue ? Math.Round(d.Value.Value * FT_TO_MM, 1) : -1;
                        string valStr = d.ValueString ?? "";
                        if (valMm == 0.0 || valStr == "0") hasZero = true;

                        segList.Add(new
                        {
                            index = 0,
                            valMm,
                            valStr,
                            text = d.ValueOverride ?? "",
                            above = d.Above ?? "",
                            below = d.Below ?? ""
                        });
                    }

                    XYZ origin = XYZ.Zero;
                    XYZ dir = XYZ.Zero;
                    if (d.Curve is Line line)
                    {
                        origin = line.Origin;
                        dir = line.Direction;
                    }

                    dimDetails.Add(new
                    {
                        id = d.Id.Value,
                        dimType = d.DimensionType?.Name,
                        numSegments = d.NumberOfSegments,
                        hasZero,
                        origin = new { x = Math.Round(origin.X * FT_TO_MM, 1), y = Math.Round(origin.Y * FT_TO_MM, 1) },
                        dir = new { x = Math.Round(dir.X, 3), y = Math.Round(dir.Y, 3) },
                        segments = segList
                    });
                }

                results.Add(new
                {
                    viewId = vId,
                    viewName = v.Name,
                    totalDims = dims.Count,
                    zeroDimsCount = dimDetails.Count(x => (bool)((dynamic)x).hasZero),
                    dims = dimDetails
                });
            }

            return new { success = true, results };
        }
    }
}
