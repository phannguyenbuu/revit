using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectCurrentSelection
    {
        private const double FT_TO_MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                var view = uidoc?.ActiveView as ViewPlan;
                if (doc == null || view == null) return new { error = "No view" };

                var selIds = uidoc.Selection.GetElementIds().ToList();

                var selectedElements = new List<object>();
                foreach (var id in selIds)
                {
                    var el = doc.GetElement(id);
                    if (el == null) continue;

                    if (el is Dimension dim)
                    {
                        var segs = new List<double>();
                        try
                        {
                            if (dim.Segments != null && dim.Segments.Size > 0)
                            {
                                foreach (DimensionSegment seg in dim.Segments)
                                {
                                    if (seg.Value.HasValue) segs.Add(Math.Round(seg.Value.Value * FT_TO_MM, 1));
                                }
                            }
                            else if (dim.Value.HasValue)
                            {
                                segs.Add(Math.Round(dim.Value.Value * FT_TO_MM, 1));
                            }
                        }
                        catch { }

                        XYZ p1 = null, p2 = null;
                        try
                        {
                            var curve = dim.Curve;
                            if (curve != null)
                            {
                                if (curve.IsBound)
                                {
                                    p1 = curve.GetEndPoint(0) * FT_TO_MM;
                                    p2 = curve.GetEndPoint(1) * FT_TO_MM;
                                }
                                else if (curve is Line l)
                                {
                                    p1 = (l.Origin - l.Direction * 10.0) * FT_TO_MM;
                                    p2 = (l.Origin + l.Direction * 10.0) * FT_TO_MM;
                                }
                            }
                        }
                        catch { }

                        var refsInfo = new List<object>();
                        try
                        {
                            if (dim.References != null)
                            {
                                foreach (Reference r in dim.References)
                                {
                                    var targetEl = doc.GetElement(r.ElementId);
                                    refsInfo.Add(new {
                                        elementId = r.ElementId.Value,
                                        cat = targetEl?.Category?.Name,
                                        name = targetEl?.Name
                                    });
                                }
                            }
                        }
                        catch { }

                        selectedElements.Add(new {
                            id = id.Value,
                            type = "Dimension",
                            dimTypeName = dim.DimensionType?.Name,
                            totalValue = dim.Value.HasValue ? Math.Round(dim.Value.Value * FT_TO_MM, 1) : 0,
                            segments = segs,
                            p1 = p1 != null ? new { x = Math.Round(p1.X, 1), y = Math.Round(p1.Y, 1) } : null,
                            p2 = p2 != null ? new { x = Math.Round(p2.X, 1), y = Math.Round(p2.Y, 1) } : null,
                            refs = refsInfo
                        });
                    }
                    else
                    {
                        selectedElements.Add(new {
                            id = id.Value,
                            type = el.GetType().Name,
                            cat = el.Category?.Name,
                            name = el.Name
                        });
                    }
                }

                return new {
                    count = selIds.Count,
                    selectedElements
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}
