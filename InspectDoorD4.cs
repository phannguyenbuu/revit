using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectDoorD4
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument.Document;
            var doorSymbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>()
                .Where(s => s.Name.Contains("D4") || s.Name.Contains("1000"))
                .Select(s => new
                {
                    id = s.Id.Value,
                    name = s.Name,
                    familyName = s.FamilyName,
                    isActive = s.IsActive
                })
                .ToList();

            var levelTum = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .FirstOrDefault(l => l.Name.Contains("TUM") || l.Id.Value == 2360635);

            var levelMai = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .FirstOrDefault(l => l.Name.Contains("MÁI") || l.Id.Value == 1209118);

            return new {
                doorSymbols,
                levelTum = levelTum != null ? new { id = levelTum.Id.Value, name = levelTum.Name, elev = levelTum.Elevation * 0.3048 } : null,
                levelMai = levelMai != null ? new { id = levelMai.Id.Value, name = levelMai.Name, elev = levelMai.Elevation * 0.3048 } : null
            };
        }
    }
}
