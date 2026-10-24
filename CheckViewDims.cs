using System;
using System.Collections.Generic;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckViewDims
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView;
            if (doc == null || view == null) return new { error = "No doc" };

            var dims = new FilteredElementCollector(doc, view.Id)
                .OfClass(typeof(Dimension))
                .Cast<Dimension>()
                .Select(d => new {
                    id = d.Id.Value,
                    name = d.Name,
                    typeName = d.DimensionType?.Name,
                    numSegments = d.Segments?.Size ?? 0,
                    totalValue = d.Value.HasValue ? Math.Round(d.Value.Value * 304.8, 1) : 0
                })
                .ToList();

            return new { viewName = view.Name, viewId = view.Id.Value, count = dims.Count, dims };
        }
    }
}
