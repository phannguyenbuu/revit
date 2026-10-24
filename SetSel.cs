using System.Collections.Generic;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class SetSel
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView;
            if (uidoc == null || doc == null || view == null) return new { error = "no uidoc/doc/view" };

            var options = args.TryGetProperty("args", out var n) && n.ValueKind == System.Text.Json.JsonValueKind.Object ? n : args;

            var ids = new List<ElementId>();
            if (options.TryGetProperty("ids", out var pIds) && pIds.ValueKind == System.Text.Json.JsonValueKind.Array)
            {
                foreach (var el in pIds.EnumerateArray())
                {
                    if (el.TryGetInt64(out var idVal)) ids.Add(new ElementId(idVal));
                }
            }
            else
            {
                // Default: select the last 2 dimensions created in the view
                var dims = new FilteredElementCollector(doc, view.Id)
                    .OfClass(typeof(Dimension))
                    .Cast<Dimension>()
                    .OrderByDescending(d => d.Id.Value)
                    .Take(2)
                    .Select(d => d.Id)
                    .ToList();
                ids.AddRange(dims);
            }

            uidoc.Selection.SetElementIds(ids);
            return new { success = true, count = ids.Count, selectedIds = ids.Select(i => i.Value).ToList() };
        }
    }
}
