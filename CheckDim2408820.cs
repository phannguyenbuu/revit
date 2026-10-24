using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckDim2408820
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var el = doc?.GetElement(new ElementId(2408820));
            if (el is Dimension dim)
            {
                var curve = dim.Curve;
                var segs = new System.Collections.Generic.List<double>();
                if (dim.Segments != null && dim.Segments.Size > 0)
                {
                    foreach (DimensionSegment s in dim.Segments)
                    {
                        if (s.Value.HasValue) segs.Add(Math.Round(s.Value.Value * 304.8, 1));
                    }
                }
                return new {
                    exists = true,
                    y = curve != null ? Math.Round(curve.GetEndPoint(0).Y * 304.8, 1) : 0,
                    segs = segs
                };
            }
            return new { exists = el != null, type = el?.GetType().Name };
        }
    }
}
