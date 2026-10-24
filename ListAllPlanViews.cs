using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ListAllPlanViews
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "no doc" };

            var views = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .Where(v => !v.IsTemplate)
                .Select(v => new {
                    id = v.Id.Value,
                    name = v.Name,
                    viewType = v.ViewType.ToString(),
                    levelName = v.GenLevel?.Name,
                    levelId = v.GenLevel?.Id.Value
                })
                .OrderBy(v => v.name)
                .ToList();

            return new { count = views.Count, views };
        }
    }
}
