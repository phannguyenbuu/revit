using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectFamilyConstraints
    {
        public static object Run(UIApplication app, System.Text.Json.JsonElement args)
        {
            string rfaPath = @"D:\Dropbox\_Documents\RevitAI\CUA_SO_2_CANH_BACKUP.rfa";
            var famDoc = app.Application.OpenDocumentFile(rfaPath);
            try
            {
                var ext = famDoc.GetElement(new ElementId(2373653L)) as Extrusion;
                var sketch = ext?.Sketch;

                var sketchInfo = new List<object>();
                if (sketch != null)
                {
                    foreach (CurveArray ca in sketch.Profile)
                    {
                        foreach (Curve c in ca)
                        {
                            sketchInfo.Add(new
                            {
                                len = c.Length * 304.8,
                                p0 = $"[{c.GetEndPoint(0).X * 304.8:F1}, {c.GetEndPoint(0).Y * 304.8:F1}, {c.GetEndPoint(0).Z * 304.8:F1}]",
                                p1 = $"[{c.GetEndPoint(1).X * 304.8:F1}, {c.GetEndPoint(1).Y * 304.8:F1}, {c.GetEndPoint(1).Z * 304.8:F1}]"
                            });
                        }
                    }
                }

                // Check all dimensions in famDoc and their references
                var dims = new List<object>();
                foreach (var d in new FilteredElementCollector(famDoc).OfClass(typeof(Dimension)).Cast<Dimension>())
                {
                    string label = "Unlabeled";
                    try { label = d.FamilyLabel?.Definition?.Name ?? "Unlabeled"; } catch { }
                    dims.Add(new
                    {
                        id = d.Id.Value,
                        label = label,
                        valMm = (d.Value ?? 0) * 304.8,
                        refCount = d.References.Size
                    });
                }

                famDoc.Close(false);

                return new
                {
                    sketchCurveCount = sketchInfo.Count,
                    sketchCurves = sketchInfo,
                    dims = dims
                };
            }
            catch (Exception ex)
            {
                try { famDoc.Close(false); } catch { }
                return new { error = ex.ToString() };
            }
        }
    }
}
