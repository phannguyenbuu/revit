using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectAllRevitLevels
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument.Document;
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .OrderBy(l => l.Elevation)
                .Select(l => new
                {
                    id = l.Id.Value,
                    name = l.Name,
                    elevationMeters = Math.Round(l.Elevation * 0.3048, 3)
                })
                .ToList();

            var views = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .Where(v => !v.IsTemplate)
                .Select(v => new
                {
                    id = v.Id.Value,
                    name = v.Name,
                    levelName = v.GenLevel?.Name,
                    viewType = v.ViewType.ToString()
                })
                .ToList();

            return new { levels, views };
        }
    }
}
