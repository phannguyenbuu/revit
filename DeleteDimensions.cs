using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class DeleteDimensions
    {
        public class WarningSwallower : IFailuresPreprocessor
        {
            public FailureProcessingResult PreprocessFailures(FailuresAccessor failuresAccessor)
            {
                failuresAccessor.DeleteAllWarnings();
                return FailureProcessingResult.Continue;
            }
        }

        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var options = args;
            if (args.TryGetProperty("args", out var nestedArgs) && nestedArgs.ValueKind == JsonValueKind.Object)
            {
                options = nestedArgs;
            }

            string scope = "file"; // default: all file
            if (options.TryGetProperty("scope", out var sProp) || args.TryGetProperty("scope", out sProp))
            {
                scope = sProp.GetString()?.ToLower() ?? "file";
            }

            long targetViewId = -1;
            if (options.TryGetProperty("viewId", out var vProp) || args.TryGetProperty("viewId", out vProp))
            {
                targetViewId = vProp.GetInt64();
            }

            var deletedIds = new List<long>();
            var failedIds = new List<long>();
            var viewBreakdown = new Dictionary<string, int>();

            using (var tx = new Transaction(doc, "Delete Dimensions"))
            {
                var fOpts = tx.GetFailureHandlingOptions();
                fOpts.SetFailuresPreprocessor(new WarningSwallower());
                tx.SetFailureHandlingOptions(fOpts);
                tx.Start();

                FilteredElementCollector collector;

                if (scope == "view" && targetViewId > 0)
                {
                    collector = new FilteredElementCollector(doc, new ElementId(targetViewId));
                }
                else if (scope == "active")
                {
                    if (uidoc.ActiveView != null)
                        collector = new FilteredElementCollector(doc, uidoc.ActiveView.Id);
                    else
                        collector = new FilteredElementCollector(doc);
                }
                else
                {
                    // "file" or "all": entire document
                    collector = new FilteredElementCollector(doc);
                }

                var dims = collector
                    .OfClass(typeof(Dimension))
                    .Cast<Dimension>()
                    .ToList();

                foreach (var d in dims)
                {
                    string viewName = "Project/Global";
                    if (d.OwnerViewId != ElementId.InvalidElementId)
                    {
                        var v = doc.GetElement(d.OwnerViewId) as View;
                        if (v != null) viewName = v.Name;
                    }

                    try
                    {
                        var idVal = d.Id.Value;
                        doc.Delete(d.Id);
                        deletedIds.Add(idVal);

                        if (!viewBreakdown.ContainsKey(viewName))
                            viewBreakdown[viewName] = 0;
                        viewBreakdown[viewName]++;
                    }
                    catch
                    {
                        failedIds.Add(d.Id.Value);
                    }
                }

                tx.Commit();
            }

            return new
            {
                success = true,
                scope,
                deletedCount = deletedIds.Count,
                failedCount = failedIds.Count,
                viewBreakdown
            };
        }
    }
}
