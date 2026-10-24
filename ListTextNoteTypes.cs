using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ListTextNoteTypes
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var types = new FilteredElementCollector(doc)
                .OfClass(typeof(TextNoteType))
                .Cast<TextNoteType>()
                .Select(t => new {
                    id = t.Id.Value,
                    name = t.Name
                })
                .ToList();

            var spotTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(SpotDimensionType))
                .Cast<SpotDimensionType>()
                .Select(s => new {
                    id = s.Id.Value,
                    name = s.Name
                })
                .ToList();

            return new { types, spotTypes };
        }
    }
}
