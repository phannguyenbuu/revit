using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectUsedDims
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var dims = new FilteredElementCollector(doc)
                .OfClass(typeof(Dimension))
                .Cast<Dimension>()
                .ToList();

            var groups = dims
                .GroupBy(d => d.DimensionType?.Name ?? "Unknown")
                .Select(g => new {
                    typeName = g.Key,
                    count = g.Count()
                })
                .OrderByDescending(x => x.count)
                .ToList();

            return new { totalDims = dims.Count, groups };
        }
    }
}
