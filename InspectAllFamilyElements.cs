using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectAllFamilyElements
    {
        public static object Run(UIApplication app, System.Text.Json.JsonElement args)
        {
            string rfaPath = @"D:\Dropbox\_Documents\RevitAI\CUA_SO_2_CANH_BACKUP.rfa";
            var famDoc = app.Application.OpenDocumentFile(rfaPath);
            try
            {
                var elements = new List<object>();
                var col = new FilteredElementCollector(famDoc)
                    .WherePasses(new LogicalOrFilter(
                        new ElementClassFilter(typeof(GenericForm)),
                        new ElementClassFilter(typeof(CurveElement))
                    ));

                foreach (var elem in col)
                {
                    string elemType = elem.GetType().Name;
                    string cat = elem.Category?.Name ?? "none";
                    long id = elem.Id.Value;

                    if (elem is Extrusion ext)
                    {
                        var bb = ext.get_BoundingBox(null);
                        elements.Add(new
                        {
                            id = id,
                            type = elemType,
                            name = ext.Name,
                            subcat = ext.Subcategory?.Name ?? "none",
                            isSolid = ext.IsSolid,
                            bb = bb != null ? $"[{bb.Min.X*304.8:F1}, {bb.Min.Y*304.8:F1}, {bb.Min.Z*304.8:F1}] to [{bb.Max.X*304.8:F1}, {bb.Max.Y*304.8:F1}, {bb.Max.Z*304.8:F1}]" : "null"
                        });
                    }
                    else if (elem is CurveElement ce)
                    {
                        var c = ce.GeometryCurve;
                        string subcat = (ce as SymbolicCurve)?.Subcategory?.Name ?? ce.LineStyle?.Name ?? "none";
                        elements.Add(new
                        {
                            id = id,
                            type = elemType,
                            subcat = subcat,
                            p0 = $"[{c.GetEndPoint(0).X * 304.8:F1}, {c.GetEndPoint(0).Y * 304.8:F1}, {c.GetEndPoint(0).Z * 304.8:F1}]",
                            p1 = $"[{c.GetEndPoint(1).X * 304.8:F1}, {c.GetEndPoint(1).Y * 304.8:F1}, {c.GetEndPoint(1).Z * 304.8:F1}]"
                        });
                    }
                }

                famDoc.Close(false);

                return new { total = elements.Count, elements };
            }
            catch (Exception ex)
            {
                try { famDoc.Close(false); } catch { }
                return new { error = ex.ToString() };
            }
        }
    }
}
