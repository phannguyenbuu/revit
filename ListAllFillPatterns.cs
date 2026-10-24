
using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ListAllFillPatterns
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var pats = new FilteredElementCollector(doc)
                .OfClass(typeof(FillPatternElement))
                .Cast<FillPatternElement>()
                .Select(p => new
                {
                    id = p.Id.Value,
                    name = p.Name,
                    target = p.GetFillPattern()?.Target.ToString()
                })
                .OrderBy(p => p.name)
                .ToList();
            return pats;
        }
    }
}
