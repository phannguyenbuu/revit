using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class DebugCreatedDimSegments
    {
        private const double FT_TO_MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            var dimIds = new long[] { 2409100, 2409101, 2409102 };
            var list = new List<object>();

            foreach (var id in dimIds)
            {
                var dim = doc.GetElement(new ElementId(id)) as Dimension;
                if (dim == null) continue;

                var segs = new List<double>();
                if (dim.Segments != null && dim.Segments.Size > 0)
                {
                    foreach (DimensionSegment s in dim.Segments)
                    {
                        if (s.Value.HasValue) segs.Add(Math.Round(s.Value.Value * FT_TO_MM, 1));
                    }
                }

                var refs = new List<object>();
                if (dim.References != null)
                {
                    foreach (Reference r in dim.References)
                    {
                        var el = doc.GetElement(r.ElementId);
                        refs.Add(new {
                            elId = r.ElementId.Value,
                            cat = el?.Category?.Name,
                            name = el?.Name
                        });
                    }
                }

                list.Add(new {
                    id,
                    totalValue = dim.Value.HasValue ? Math.Round(dim.Value.Value * FT_TO_MM, 1) : 0,
                    segCount = segs.Count,
                    segments = segs,
                    refs
                });
            }

            return new { list };
        }
    }
}
