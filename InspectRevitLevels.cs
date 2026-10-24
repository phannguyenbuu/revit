using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectRevitLevels
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument.Document;
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .OrderBy(l => l.Elevation)
                .Select(l => new {
                    id = l.Id.Value,
                    name = l.Name,
                    elevM = l.Elevation * 0.3048
                })
                .ToList();

            var stairTypes = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Stairs)
                .WhereElementIsElementType()
                .Select(t => new { id = t.Id.Value, name = t.Name, type = t.GetType().Name })
                .ToList();

            return new { levels, stairTypes };
        }
    }
}
