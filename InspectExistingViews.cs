using System;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectExistingViews
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };
            var views = new FilteredElementCollector(doc)
                .OfClass(typeof(View))
                .Cast<View>()
                .Where(v => !v.IsTemplate)
                .Select(v => new {
                    id = v.Id.Value,
                    name = v.Name,
                    viewType = v.ViewType.ToString(),
                    vftName = doc.GetElement(v.GetTypeId())?.Name,
                    isCallout = v.IsCallout
                })
                .Where(v => v.name.Contains("CHI TIẾT") || v.name.Contains("THANG") || v.name.Contains("VỆ SINH") || v.name.Contains("Callout") || v.isCallout)
                .ToList();
            return views;
        }
    }
}
