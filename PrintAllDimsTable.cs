using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class PrintAllDimsTable
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
                    XYZ origin = XYZ.Zero;
                    XYZ dir = XYZ.BasisX;
                    if (c != null)
                    {
                        if (c.IsBound)
                        {
                            origin = c.GetEndPoint(0);
                            dir = (c.GetEndPoint(1) - c.GetEndPoint(0)).Normalize();
                        }
                        else if (c is Line l)
                        {
                            origin = l.Origin;
                            dir = l.Direction;
                        }
                    }
                    bool isX = Math.Abs(dir.X) > 0.8;
                    double pos = isX ? origin.Y * FT_TO_MM : origin.X * FT_TO_MM;
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
                    return new {
                        id = d.Id.Value,
                        dir = isX ? "HORIZ (X)" : "VERT (Y)",
                        pos = Math.Round(pos, 0),
                        segCount = segs.Count,
                        segs = string.Join(", ", segs)
                    };
                })
                .ToList();

            return dims;
        }
    }
}
