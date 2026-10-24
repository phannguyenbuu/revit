using System;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectTextNoteMethods
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var textMethods = typeof(TextNote).GetMethods(BindingFlags.Public | BindingFlags.Static)
                .Where(m => m.Name == "Create")
                .Select(m => m.Name + "(" + string.Join(", ", m.GetParameters().Select(p => p.ParameterType.Name + " " + p.Name)) + ")")
                .Distinct()
                .OrderBy(s => s)
                .ToList();

            var doc = uiapp.ActiveUIDocument.Document;
            var existingTextNotes = new FilteredElementCollector(doc, uiapp.ActiveUIDocument.ActiveView.Id)
                .OfClass(typeof(TextNote))
                .Cast<TextNote>()
                .Select(t => new {
                    id = t.Id.Value,
                    text = t.Text,
                    origin = new { x = t.Coord.X * 0.3048, y = t.Coord.Y * 0.3048 },
                    typeName = doc.GetElement(t.GetTypeId())?.Name
                })
                .ToList();

            return new { textMethods, existingTextNotes };
        }
    }
}
