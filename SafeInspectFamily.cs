using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class SafeInspectFamily
    {
        public static object Run(UIApplication app, System.Text.Json.JsonElement args)
        {
            try
            {
                var doc = app.ActiveUIDocument?.Document;
                if (doc == null) return new { error = "No doc" };
                var win = doc.GetElement(new ElementId(2361245L)) as FamilyInstance;
                if (win == null) return new { error = "No win" };

                var fam = win.Symbol.Family;
                Document famDoc = null;
                famDoc = doc.EditFamily(fam);

            if (famDoc == null) return new { error = "famDoc is null" };

            var refPlanes = new FilteredElementCollector(famDoc)
                .OfClass(typeof(ReferencePlane))
                .Cast<ReferencePlane>()
                .Select(rp => new {
                    name = rp.Name,
                    dir = $"[{rp.Direction.X:F2}, {rp.Direction.Y:F2}, {rp.Direction.Z:F2}]",
                    origin = $"[{rp.FreeEnd.X*304.8:F1}, {rp.FreeEnd.Y*304.8:F1}, {rp.FreeEnd.Z*304.8:F1}]"
                })
                .ToList();

            var dimensions = new List<object>();
            foreach (var d in new FilteredElementCollector(famDoc).OfClass(typeof(Dimension)).Cast<Dimension>())
            {
                string label = "Unlabeled";
                try { label = d.FamilyLabel?.Definition?.Name ?? "Unlabeled"; } catch {}
                dimensions.Add(new {
                    id = d.Id.Value,
                    name = label,
                    valMm = (d.Value ?? 0) * 304.8
                });
            }

            var fm = famDoc.FamilyManager;
            var curType = fm.CurrentType;
            var paramDict = new Dictionary<string, string>();
            foreach (FamilyParameter fp in fm.Parameters)
            {
                string formula = fp.Formula ?? "";
                string val = "";
                if (curType != null && curType.HasValue(fp))
                {
                    val = fp.StorageType == StorageType.Double ? $"{(curType.AsDouble(fp) ?? 0) * 304.8:F1} mm" : curType.AsString(fp) ?? "";
                }
                paramDict[fp.Definition.Name] = $"{val} (Formula: {formula})";
            }

            // Also check all extrusions and their sketch planes / profiles
            var extrusions = new FilteredElementCollector(famDoc)
                .OfClass(typeof(Extrusion))
                .Cast<Extrusion>()
                .Select(e => {
                    var curves = new List<string>();
                    try {
                        foreach (CurveArray ca in e.Sketch?.Profile ?? new CurveArrArray()) {
                            foreach (Curve c in ca) {
                                curves.Add($"{c.GetType().Name}: {c.GetEndPoint(0)*304.8} -> {c.GetEndPoint(1)*304.8}");
                            }
                        }
                    } catch {}
                    return new {
                        id = e.Id.Value,
                        isSolid = e.IsSolid,
                        sketchPlane = e.Sketch?.SketchPlane?.Name ?? "none",
                        curveCount = curves.Count,
                        curves = curves.Take(10).ToList()
                    };
                })
                .ToList();

            // Save a copy of family for safe keeping
            try
            {
                famDoc.SaveAs(@"D:\Dropbox\_Documents\RevitAI\CUA_SO_2_CANH_BACKUP.rfa", new SaveAsOptions { OverwriteExistingFile = true });
            }
            catch {}

            // Don't close famDoc immediately if it causes Revit to close; 
            // In fact, closing famDoc is safe if we don't close the last doc or if we close cleanly.
            famDoc.Close(false);

            return new
            {
                currentType = curType?.Name,
                paramsInfo = paramDict,
                dimensions = dimensions,
                refPlanes = refPlanes,
                extrusions = extrusions
            };
        }
        catch (Exception ex)
        {
            return new { error = ex.ToString() };
        }
    }
}
}
