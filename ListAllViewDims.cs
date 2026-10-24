using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ListAllViewDims
    {
        private const double FT_TO_MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            var dims = new FilteredElementCollector(doc, view.Id)
                .OfClass(typeof(Dimension))
                .Cast<Dimension>()
                .Select(d => {
                    var c = d.Curve;
                    var p1 = c != null && c.IsBound ? c.GetEndPoint(0) * FT_TO_MM : null;
                    var p2 = c != null && c.IsBound ? c.GetEndPoint(1) * FT_TO_MM : null;
                    var segs = new List<double>();
                    if (d.Segments != null && d.Segments.Size > 0)
                    {
                        foreach (DimensionSegment s in d.Segments)
                        {
                            if (s.Value.HasValue) segs.Add(Math.Round(s.Value.Value * FT_TO_MM, 0));
                        }
                    }
                    else if (d.Value.HasValue)
                    {
                        segs.Add(Math.Round(d.Value.Value * FT_TO_MM, 0));
                    }
                    bool isHoriz = p1 != null && p2 != null && Math.Abs(p1.Y - p2.Y) < 1.0;
                    return new {
                        id = d.Id.Value,
                        name = d.Name,
                        typeName = d.DimensionType?.Name,
                        isHoriz = isHoriz,
                        coord = isHoriz ? Math.Round(p1.Y, 0) : (p1 != null ? Math.Round(p1.X, 0) : 0),
                        segCount = segs.Count,
                        segs = segs
                    };
                })
                .ToList();

            return new { count = dims.Count, dims };
        }
    }
}
