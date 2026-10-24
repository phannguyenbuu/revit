using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectHeadlessFamily
    {
        public static object Run(UIApplication app, System.Text.Json.JsonElement args)
        {
            string rfaPath = @"D:\Dropbox\_Documents\RevitAI\CUA_SO_2_CANH_BACKUP.rfa";
            if (!File.Exists(rfaPath)) return new { error = "RFA not found: " + rfaPath };

            Document famDoc = null;
            try
            {
                famDoc = app.Application.OpenDocumentFile(rfaPath);
                if (famDoc == null) return new { error = "Failed to open document headless" };

                var fm = famDoc.FamilyManager;
                var paramList = new List<object>();
                foreach (FamilyParameter fp in fm.Parameters)
                {
                    string defName = fp.Definition.Name;
                    paramList.Add(new
                    {
                        name = defName,
                        formula = fp.Formula ?? "",
                        isInstance = fp.IsInstance,
                        storageType = fp.StorageType.ToString()
                    });
                }

                var dims = new List<object>();
                foreach (var d in new FilteredElementCollector(famDoc).OfClass(typeof(Dimension)).Cast<Dimension>())
                {
                    string label = "Unlabeled";
                    try { label = d.FamilyLabel?.Definition?.Name ?? "Unlabeled"; } catch { }
                    dims.Add(new
                    {
                        id = d.Id.Value,
                        label = label,
                        valueMm = (d.Value ?? 0) * 304.8,
                        numSegments = d.Segments?.Size ?? 0
                    });
                }

                var refPlanes = new FilteredElementCollector(famDoc)
                    .OfClass(typeof(ReferencePlane))
                    .Cast<ReferencePlane>()
                    .Select(rp => new
                    {
                        name = rp.Name,
                        bubble = $"[{rp.BubbleEnd.X * 304.8:F1}, {rp.BubbleEnd.Y * 304.8:F1}, {rp.BubbleEnd.Z * 304.8:F1}]",
                        free = $"[{rp.FreeEnd.X * 304.8:F1}, {rp.FreeEnd.Y * 304.8:F1}, {rp.FreeEnd.Z * 304.8:F1}]"
                    })
                    .ToList();

                var extrusions = new List<object>();
                foreach (var ext in new FilteredElementCollector(famDoc).OfClass(typeof(Extrusion)).Cast<Extrusion>())
                {
                    var curves = new List<string>();
                    try
                    {
                        if (ext.Sketch != null)
                        {
                            foreach (CurveArray ca in ext.Sketch.Profile)
                            {
                                foreach (Curve c in ca)
                                {
                                    curves.Add($"{c.GetType().Name}: [{c.GetEndPoint(0).X * 304.8:F1}, {c.GetEndPoint(0).Y * 304.8:F1}, {c.GetEndPoint(0).Z * 304.8:F1}] -> [{c.GetEndPoint(1).X * 304.8:F1}, {c.GetEndPoint(1).Y * 304.8:F1}, {c.GetEndPoint(1).Z * 304.8:F1}]");
                                }
                            }
                        }
                    }
                    catch (Exception ex)
                    {
                        curves.Add("Err: " + ex.Message);
                    }

                    extrusions.Add(new
                    {
                        id = ext.Id.Value,
                        isSolid = ext.IsSolid,
                        startMm = ext.StartOffset * 304.8,
                        endMm = ext.EndOffset * 304.8,
                        curveCount = curves.Count,
                        curves = curves
                    });
                }

                famDoc.Close(false);

                return new
                {
                    success = true,
                    parameters = paramList,
                    dimensions = dims,
                    refPlanes = refPlanes,
                    extrusions = extrusions
                };
            }
            catch (Exception ex)
            {
                if (famDoc != null) try { famDoc.Close(false); } catch { }
                return new { error = ex.ToString() };
            }
        }
    }
}
