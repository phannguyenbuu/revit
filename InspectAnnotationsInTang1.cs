using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectAnnotationsInTang1
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var view = uiapp.ActiveUIDocument?.ActiveView;
            if (doc == null || view == null) return new { error = "No doc or view" };

            var texts = new FilteredElementCollector(doc, view.Id)
                .OfClass(typeof(TextNote))
                .Cast<TextNote>()
                .Select(t => new {
                    text = t.Text,
                    x = t.Coord.X * 304.8,
                    y = t.Coord.Y * 304.8
                })
                .Where(t => t.text.Contains("0.") || t.text.Contains("âm") || t.text.Contains("hạ") || t.text.Contains("WC") || t.text.Contains("-") || t.text.Contains("▼") || t.text.Contains("cốt") || t.text.Contains("cos"))
                .Take(30)
                .ToList();

            var spots = new FilteredElementCollector(doc, view.Id)
                .OfClass(typeof(SpotDimension))
                .Cast<SpotDimension>()
                .Select(s => new {
                    id = s.Id.Value,
                    name = s.Name,
                    x = s.Origin.X * 304.8,
                    y = s.Origin.Y * 304.8
                })
                .Take(20)
                .ToList();

            return new { texts, spots };
        }
    }
}
