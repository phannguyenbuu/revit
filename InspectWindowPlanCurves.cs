using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectWindowPlanCurves
    {
        public static object Run(UIApplication app, System.Text.Json.JsonElement args)
        {
            var doc = app.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };
            var win = doc.GetElement(new ElementId(2361245L)) as FamilyInstance;
            if (win == null) return new { error = "No win" };

            var view = doc.ActiveView;

            var opt = new Options
            {
                View = view,
                IncludeNonVisibleObjects = true
            };

            var geom = win.get_Geometry(opt);
            var lines = new List<object>();

            if (geom != null)
            {
                foreach (var obj in geom)
                {
                    if (obj is GeometryInstance gi)
                    {
                        var instGeom = gi.GetInstanceGeometry();
                        foreach (var g in instGeom)
                        {
                            if (g is Line l)
                            {
                                var p0 = l.GetEndPoint(0);
                                var p1 = l.GetEndPoint(1);
                                lines.Add(new
                                {
                                    type = "InstanceLine",
                                    graphicsStyle = doc.GetElement(l.GraphicsStyleId)?.Name ?? "none",
                                    p0 = $"[{p0.X*304.8:F1}, {p0.Y*304.8:F1}, {p0.Z*304.8:F1}]",
                                    p1 = $"[{p1.X*304.8:F1}, {p1.Y*304.8:F1}, {p1.Z*304.8:F1}]",
                                    len = l.Length * 304.8
                                });
                            }
                            else if (g is Solid s && s.Volume > 0.0001)
                            {
                                var bb = s.GetBoundingBox();
                                lines.Add(new
                                {
                                    type = "PlanSolid",
                                    min = $"[{bb.Min.X*304.8:F1}, {bb.Min.Y*304.8:F1}, {bb.Min.Z*304.8:F1}]",
                                    max = $"[{bb.Max.X*304.8:F1}, {bb.Max.Y*304.8:F1}, {bb.Max.Z*304.8:F1}]"
                                });
                            }
                        }
                    }
                    else if (obj is Line l)
                    {
                        var p0 = l.GetEndPoint(0);
                        var p1 = l.GetEndPoint(1);
                        lines.Add(new
                        {
                            type = "DirectLine",
                            p0 = $"[{p0.X*304.8:F1}, {p0.Y*304.8:F1}, {p0.Z*304.8:F1}]",
                            p1 = $"[{p1.X*304.8:F1}, {p1.Y*304.8:F1}, {p1.Z*304.8:F1}]"
                        });
                    }
                }
            }

            return new
            {
                view = view.Name,
                winLoc = (win.Location as LocationPoint)?.Point is XYZ p ? $"[{p.X*304.8:F1}, {p.Y*304.8:F1}, {p.Z*304.8:F1}]" : "none",
                lineCount = lines.Count,
                lines
            };
        }
    }
}
