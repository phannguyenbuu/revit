using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class SetDoorsAndWindowsFrameInside
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active document" };

            var symbols = new FilteredElementCollector(doc)
                .WherePasses(new ElementMulticategoryFilter(new List<BuiltInCategory> { BuiltInCategory.OST_Doors, BuiltInCategory.OST_Windows }))
                .OfClass(typeof(FamilySymbol))
                .Cast<FamilySymbol>()
                .ToList();

            var modified = new List<object>();

            using (var trans = new Transaction(doc, "Set Frame Inside and Outside Size Standard"))
            {
                var fOpts = trans.GetFailureHandlingOptions();
                fOpts.SetFailuresPreprocessor(new SyncWarningSwallower());
                trans.SetFailureHandlingOptions(fOpts);
                trans.Start();

                foreach (var s in symbols)
                {
                    bool changed = false;
                    var changes = new List<string>();

                    // 1. Frame Projection Ext. / TrimProjection / Trim Projection Ext -> 0
                    string[] extProjParamNames = new string[] {
                        "Frame Projection Ext.",
                        "TrimProjection",
                        "Trim Projection Ext",
                        "Trim Projection Ext.",
                        "25" // In CUA SO 2 CANH NHOM KINH, param "25" is the exterior trim projection
                    };

                    foreach (var pName in extProjParamNames)
                    {
                        var p = s.LookupParameter(pName);
                        if (p != null && !p.IsReadOnly && p.StorageType == StorageType.Double)
                        {
                            double oldVal = p.AsDouble() * 304.8;
                            if (oldVal > 0.001)
                            {
                                p.Set(0.0);
                                changes.Add($"{pName}: {oldVal:F1}mm -> 0mm");
                                changed = true;
                            }
                        }
                    }

                    // 2. Align Rough Width/Height with nominal Width/Height if present (Outside dimension standard)
                    var pWidth = s.LookupParameter("Width");
                    var pRoughWidth = s.LookupParameter("Rough Width");
                    if (pWidth != null && pRoughWidth != null && !pRoughWidth.IsReadOnly)
                    {
                        double w = pWidth.AsDouble();
                        double rw = pRoughWidth.AsDouble();
                        if (Math.Abs(w - rw) > 0.001)
                        {
                            pRoughWidth.Set(w);
                            changes.Add($"Rough Width: {rw * 304.8:F1}mm -> {w * 304.8:F1}mm");
                            changed = true;
                        }
                    }

                    var pHeight = s.LookupParameter("Height");
                    var pRoughHeight = s.LookupParameter("Rough Height");
                    if (pHeight != null && pRoughHeight != null && !pRoughHeight.IsReadOnly)
                    {
                        double h = pHeight.AsDouble();
                        double rh = pRoughHeight.AsDouble();
                        if (Math.Abs(h - rh) > 0.001)
                        {
                            pRoughHeight.Set(h);
                            changes.Add($"Rough Height: {rh * 304.8:F1}mm -> {h * 304.8:F1}mm");
                            changed = true;
                        }
                    }

                    if (changed)
                    {
                        modified.Add(new
                        {
                            category = s.Category.Name,
                            family = s.FamilyName,
                            type = s.Name,
                            changes = changes
                        });
                    }
                }

                trans.Commit();
            }

            return new
            {
                success = true,
                modifiedCount = modified.Count,
                modifiedTypes = modified
            };
        }
    }
}
